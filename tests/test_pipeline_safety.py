import os
import subprocess
import sys
import tempfile
import unittest
import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from pipeline_common import content_label, drive_local_path

analyzer_spec = importlib.util.spec_from_loader(
    "analizar_y_versionar_pdfs",
    SourceFileLoader("analizar_y_versionar_pdfs", str(SCRIPTS / "analizar-y-versionar-pdfs")),
)
analyzer = importlib.util.module_from_spec(analyzer_spec)
analyzer_spec.loader.exec_module(analyzer)

renamer_spec = importlib.util.spec_from_loader(
    "etapa_1_renombrado",
    SourceFileLoader("etapa_1_renombrado", str(SCRIPTS / "etapa-1-renombrado")),
)
renamer = importlib.util.module_from_spec(renamer_spec)
renamer_spec.loader.exec_module(renamer)

excel_spec = importlib.util.spec_from_loader(
    "etapa_2_extraccion_exceles",
    SourceFileLoader("etapa_2_extraccion_exceles", str(SCRIPTS / "etapa-2-extraccion-exceles")),
)
excel_stage = importlib.util.module_from_spec(excel_spec)
excel_spec.loader.exec_module(excel_stage)

drive_rename_spec = importlib.util.spec_from_loader(
    "actualizar_nombres_drive_desde_manifest",
    SourceFileLoader("actualizar_nombres_drive_desde_manifest", str(SCRIPTS / "actualizar-nombres-drive-desde-manifest")),
)
drive_rename = importlib.util.module_from_spec(drive_rename_spec)
drive_rename_spec.loader.exec_module(drive_rename)

notebooklm_spec = importlib.util.spec_from_loader(
    "preparar_notebooklm_por_estado",
    SourceFileLoader("preparar_notebooklm_por_estado", str(SCRIPTS / "preparar-notebooklm-por-estado")),
)
notebooklm = importlib.util.module_from_spec(notebooklm_spec)
notebooklm_spec.loader.exec_module(notebooklm)

notebooklm_drive_spec = importlib.util.spec_from_loader(
    "sincronizar_notebooklm_drive",
    SourceFileLoader("sincronizar_notebooklm_drive", str(SCRIPTS / "sincronizar-notebooklm-drive")),
)
notebooklm_drive = importlib.util.module_from_spec(notebooklm_drive_spec)
notebooklm_drive_spec.loader.exec_module(notebooklm_drive)

exceles_drive_spec = importlib.util.spec_from_loader(
    "sincronizar_exceles_drive",
    SourceFileLoader("sincronizar_exceles_drive", str(SCRIPTS / "sincronizar-exceles-drive")),
)
exceles_drive = importlib.util.module_from_spec(exceles_drive_spec)
exceles_drive_spec.loader.exec_module(exceles_drive)


def run(script, *arguments, work_dir):
    environment = {**os.environ, "FASP_WORK_DIR": str(work_dir)}
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *map(str, arguments)],
        capture_output=True,
        text=True,
        env=environment,
    )


class PipelineSafetyTests(unittest.TestCase):
    def test_drive_ids_produce_distinct_local_paths_for_the_same_name(self):
        first = drive_local_path("01 EdoMex/DOC-DOCUMENTO_V1.0.pdf", "id-one")
        second = drive_local_path("01 EdoMex/DOC-DOCUMENTO_V1.0.pdf", "id-two")
        self.assertNotEqual(first, second)
        self.assertEqual(first.parent, second.parent)

    def test_content_label_uses_pdf_title_or_first_heading(self):
        self.assertEqual(content_label("\n\nLey de Ingresos del Estado\nArtículo 1", ""), "LEY_DE_INGRESOS_DEL_ESTADO")
        self.assertEqual(content_label("contenido", "Informe de evaluación 2025"), "INFORME_DE_EVALUACION_2025")

    def test_content_version_name_is_readable_without_hash(self):
        name = analyzer.human_target_name(
            Path("FASP_2026_P1_MEX_DOC-DOCUMENTO_V1.0__drive-abc123.pdf"),
            "Toluca de Lerdo México",
            duplicate_index=2,
        )
        self.assertEqual(name, "FASP_2026_P1_MEX_DOC_DOCUMENTO_TOLUCA-DE-LERDO-MEXICO_V1.2.pdf")
        self.assertNotIn("abc123", name)
        self.assertNotIn("__", name)

    def test_normalize_filename_preserves_readable_version(self):
        name = renamer.normalize_filename("FASP_2026_P1_MEX_DOC-DOCUMENTO_Toluca de Lerdo México_V1.2.pdf")
        self.assertEqual(name, "FASP_2026_P1_MEX_DOC-DOCUMENTO_TOLUCA_DE_LERDO_MEXICO_V1.2.pdf")

    def test_drive_rename_resolves_file_id_from_manifest_original_name(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_dir = root / "09 FASP" / "01 EdoMex"
            manifest_dir.mkdir(parents=True)
            file_id = "1aTq-ON0oonP9HOOv2FF8zSVyXqr3JLFh"
            (manifest_dir / "contenido_manifest.json").write_text(
                """
                {
                  "files": [
                    {
                      "original_name": "FASP_2026_P1_MEX_DOC-DOCUMENTO_V1.0__drive-1aTqON0oonP9HOOv.pdf",
                      "final_name": "FASP_2026_P1_MEX_DOC_DOCUMENTO_LA-INFORMACION_V1.0.pdf"
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            updates = drive_rename.build_updates(root / "09 FASP", {"files": {file_id: {}}})
            self.assertEqual(updates[0]["status"], "pendiente")
            self.assertEqual(updates[0]["file_id"], file_id)

    def test_drive_rename_prefers_explicit_drive_file_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest_dir = root / "09 FASP" / "01 EdoMex"
            manifest_dir.mkdir(parents=True)
            file_id = "explicit-id"
            (manifest_dir / "contenido_manifest.json").write_text(
                """
                {
                  "files": [
                    {
                      "original_name": "FASP_2026_P1_MEX_DOC_DOCUMENTO_V1.0.pdf",
                      "final_name": "FASP_2026_P1_MEX_DOC_DOCUMENTO_V1.0.pdf",
                      "drive_file_id": "explicit-id"
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            updates = drive_rename.build_updates(root / "09 FASP", {"files": {}})
            self.assertEqual(updates[0]["status"], "pendiente")
            self.assertEqual(updates[0]["file_id"], file_id)

    def test_drive_rename_missing_file_id_is_blocking(self):
        updates = [{"status": "sin_file_id", "final_name": "FASP_DOC_V1.0.pdf"}]
        report = {"status_counts": {}}
        for item in updates:
            report["status_counts"][item["status"]] = report["status_counts"].get(item["status"], 0) + 1
        self.assertTrue(any(report["status_counts"].get(status, 0) for status in {"error", "sin_file_id", "file_id_no_resuelto"}))

    def test_excel_stage_includes_common_sources_for_state_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            common_bib = root / "00 Bibliografía y normatividad federal" / "01 Bibliografía"
            common_federal = root / "00 Bibliografía y normatividad federal" / "02 Normatividad federal"
            state = root / "01 EdoMex Nancy G"
            common_bib.mkdir(parents=True)
            common_federal.mkdir(parents=True)
            state.mkdir()
            (common_bib / "FASP_2026_P1_NAL_BIB-ARTICULO_V1.0.pdf").write_bytes(b"bib")
            (common_federal / "FASP_2026_P1_NAL_NORFED-LEY_V1.0.pdf").write_bytes(b"federal")
            (state / "FASP_2026_P1_MEX_DOC-DOCUMENTO_V1.0.pdf").write_bytes(b"state")
            previous_common = excel_stage.COMMON_DIR
            excel_stage.COMMON_DIR = root / "00 Bibliografía y normatividad federal"
            try:
                files = excel_stage.input_pdfs(state, include_common=True)
            finally:
                excel_stage.COMMON_DIR = previous_common
            self.assertEqual([item.name for item in files], [
                "FASP_2026_P1_NAL_BIB-ARTICULO_V1.0.pdf",
                "FASP_2026_P1_NAL_NORFED-LEY_V1.0.pdf",
                "FASP_2026_P1_MEX_DOC-DOCUMENTO_V1.0.pdf",
            ])

    def test_excel_stage_deduplicates_common_sources_by_sha(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            common_bib = root / "00 Bibliografía y normatividad federal" / "01 Bibliografía"
            state = root / "01 EdoMex Nancy G"
            common_bib.mkdir(parents=True)
            state.mkdir()
            (common_bib / "FASP_2026_P1_NAL_BIB-ARTICULO_V1.0.pdf").write_bytes(b"same")
            (state / "FASP_2026_P1_NAL_BIB-ARTICULO_V1.0.pdf").write_bytes(b"same")
            previous_common = excel_stage.COMMON_DIR
            excel_stage.COMMON_DIR = root / "00 Bibliografía y normatividad federal"
            try:
                files = excel_stage.input_pdfs(state, include_common=True)
            finally:
                excel_stage.COMMON_DIR = previous_common
            self.assertEqual(len(files), 1)

    def test_excel_stage_infers_readable_title_from_text_or_filename(self):
        title, source = excel_stage.inferred_title(Path("FASP_2026_P1_NAL_BIB-ARTICULO-06_V1.0.pdf"), "", "Coordinación institucional para seguridad pública")
        self.assertEqual(title, "Coordinacion Institucional Para Seguridad Publica")
        self.assertEqual(source, "texto_pdf")
        title, source = excel_stage.inferred_title(Path("FASP_2026_P1_NAL_BIB-ARTICULO-06_V1.0.pdf"), "", "")
        self.assertEqual(title, "Articulo 06")
        self.assertEqual(source, "nombre_archivo")

    def test_excel_stage_normalizes_pdf_creation_date(self):
        self.assertEqual(excel_stage.clean_pdf_date("D:20260725183000-06'00'"), "2026-07-25")
        self.assertEqual(excel_stage.clean_pdf_date("2026"), "2026")

    def test_rename_keeps_non_identical_name_collision(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            source.mkdir()
            (source / "a b.pdf").write_bytes(b"first")
            (source / "A_B.pdf").write_bytes(b"second")
            result = run("etapa-1-renombrado", "--source", source, work_dir=Path(temporary))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(list(source.glob("*.pdf"))), 2)
            self.assertTrue(any("_COPIA-2" in item.name for item in source.glob("*.pdf")))

    def test_integration_rejects_flattening_collision_before_modifying_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            (source / "one").mkdir(parents=True)
            (source / "two").mkdir()
            (source / "one" / "same.pdf").write_bytes(b"one")
            (source / "two" / "same.pdf").write_bytes(b"two")
            output = root / "corpus"
            output.mkdir()
            sentinel = output / "existing.pdf"
            sentinel.write_bytes(b"keep")
            result = run("etapa-3-integracion-corpusintegrado", "--source", source, "--output", output, work_dir=root)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(sentinel.read_bytes(), b"keep")

    def test_distribution_replaces_previous_result_without_stale_pdfs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "FASP_MEX_LEY.pdf").write_bytes(b"document")
            output = root / "distribution"
            stale = output / "Hidalgo" / "00_Otros" / "stale.pdf"
            stale.parent.mkdir(parents=True)
            stale.write_bytes(b"stale")
            result = run("etapa-4-distribucion-por-estado", "--source", corpus, "--output", output, work_dir=root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(stale.exists())
            self.assertTrue((output / "Estado_de_Mexico" / "02_Normatividad_Estatal" / "FASP_MEX_LEY.pdf").exists())

    def test_notebooklm_copy_section_deduplicates_by_sha(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            output = root / "out"
            source.mkdir()
            first = source / "a.pdf"
            second = source / "b.pdf"
            first.write_bytes(b"same")
            second.write_bytes(b"same")
            records = notebooklm.copy_section([first, second], output, root)
            self.assertEqual(len(records), 1)
            self.assertEqual(len(list(output.glob("*.pdf"))), 1)

    def test_notebooklm_index_contains_three_sections(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            notebooklm.write_index(state_dir, "01 EdoMex Nancy G", {
                "00_Bibliografia": [],
                "01_Normativa_Federal": [],
                "02_Normativa_Estatal": [],
            })
            text = (state_dir / "FUENTES_NOTEBOOKLM.md").read_text(encoding="utf-8")
            self.assertIn("00_Bibliografia", text)
            self.assertIn("01_Normativa_Federal", text)
            self.assertIn("02_Normativa_Estatal", text)

    def test_notebooklm_drive_query_escapes_apostrophes(self):
        self.assertEqual(notebooklm_drive.quote_query_value("FASP's Folder"), "FASP\\'s Folder")

    def test_notebooklm_drive_dry_run_does_not_query_virtual_parent(self):
        class Files:
            def list(self, **kwargs):
                raise AssertionError("No debe consultar Drive para carpetas padre virtuales")

        class Service:
            def files(self):
                return Files()

        folder_id, status = notebooklm_drive.ensure_folder(Service(), "dry-run:root/FASP_NBLM", "01 EdoMex", dry_run=True)
        self.assertEqual(status, "carpeta_crear")
        self.assertEqual(folder_id, "dry-run:root/FASP_NBLM/01 EdoMex")

    def test_notebooklm_drive_manifest_is_not_uploaded_as_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / "a.pdf").write_bytes(b"source")
            (source / "notebooklm_drive_manifest.json").write_text("{}", encoding="utf-8")
            names = [path.name for path in notebooklm_drive.iter_local_files(source)]
            self.assertEqual(names, ["a.pdf"])

    def test_notebooklm_drive_novelty_candidates_include_only_new_or_changed_files(self):
        actions = [
            {"type": "file", "status": "sin_cambios", "path": "a.pdf"},
            {"type": "file", "status": "subido", "path": "b.pdf"},
            {"type": "file", "status": "actualizado", "path": "c.pdf"},
            {"type": "folder", "status": "carpeta_creada", "path": "folder"},
        ]
        paths = [item["path"] for item in notebooklm_drive.novelty_candidates(actions)]
        self.assertEqual(paths, ["b.pdf", "c.pdf"])

    def test_notebooklm_drive_dry_run_creates_novelties_for_new_files(self):
        class Files:
            def list(self, **kwargs):
                class Request:
                    def execute(self):
                        return {"files": []}
                return Request()

        class Service:
            def files(self):
                return Files()

        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "notebooklm"
            nested = source / "01 EdoMex Nancy G" / "02_Normativa_Estatal"
            nested.mkdir(parents=True)
            (nested / "a.pdf").write_bytes(b"new")
            report = notebooklm_drive.sync_tree(
                Service(),
                source,
                "FASP_NBLM",
                "root",
                dry_run=True,
                novedades_root_name="FASP_NBLM_NOVEDADES",
                run_label="2026-07-25",
                create_novelties=True,
            )
            self.assertEqual(report["status_counts"]["subir"], 1)
            self.assertEqual(report["status_counts"]["novedad_subir"], 1)
            self.assertIn("novedad_carpeta_crear", report["status_counts"])

    def test_notebooklm_drive_unchanged_file_uses_sha_property(self):
        class Files:
            def list(self, **kwargs):
                class Request:
                    def execute(self):
                        return {"files": [{"id": "file-id", "name": "a.pdf", "appProperties": {"fasp_sha256": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"}}]}
                return Request()

        class Service:
            def files(self):
                return Files()

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "notebooklm"
            source.mkdir()
            pdf = source / "a.pdf"
            pdf.write_bytes(b"hello")
            result = notebooklm_drive.sync_file(Service(), pdf, source, "parent", dry_run=False)
            self.assertEqual(result["status"], "sin_cambios")
            self.assertEqual(result["drive_id"], "file-id")

    def test_exceles_drive_manifest_is_not_uploaded_as_excel_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary)
            (source / "a.xlsx").write_bytes(b"source")
            (source / "exceles_drive_manifest.json").write_text("{}", encoding="utf-8")
            names = [path.name for path in exceles_drive.iter_local_files(source)]
            self.assertEqual(names, ["a.xlsx"])

    def test_exceles_drive_unchanged_file_uses_sha_property(self):
        class Files:
            def list(self, **kwargs):
                class Request:
                    def execute(self):
                        return {"files": [{"id": "file-id", "name": "a.xlsx", "appProperties": {"fasp_sha256": "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"}}]}
                return Request()

        class Service:
            def files(self):
                return Files()

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "exceles"
            source.mkdir()
            xlsx = source / "a.xlsx"
            xlsx.write_bytes(b"hello")
            result = exceles_drive.sync_file(Service(), xlsx, source, "parent", dry_run=False)
            self.assertEqual(result["status"], "sin_cambios")
            self.assertEqual(result["drive_id"], "file-id")


if __name__ == "__main__":
    unittest.main()
