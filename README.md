# FASP Pipeline Multiagente V3

Pipeline para sincronizar, normalizar, analizar y distribuir documentos FASP.

## Estado

El pipeline está preparado para ejecuciones reproducibles. Cada estado se procesa en sus propias salidas; la carga a Drive se ejecuta como una operación global separada.

El flujo es incremental: puede correrse durante varios días sobre la misma carpeta. Los archivos ya versionados se reconocen por su SHA y por `drive_file_id` en `contenido_manifest.json`; no deben re-versionarse como documentos nuevos.

## Requisitos

- Python 3.8 o posterior.
- Dependencias: `python3 -m pip install -r requirements.txt`.
- Token de Google Drive en `~/.hermes/google_token.json`, o en la ruta indicada por `FASP_GOOGLE_TOKEN`.
- Directorio de trabajo mediante `FASP_WORK_DIR`; si se omite, usa `/Users/adominguezdia/Documents/FASP`.

## Carpeta local de trabajo

La carpeta indicada por `FASP_WORK_DIR` es solo el área operativa de datos. No debe usarse como repositorio Git ni como almacén de scripts, reportes históricos o bitácoras de pruebas. Después de una limpieza o corrida base debe conservar únicamente:

- `09 FASP`
- `corpusintegrado`
- `corpus_por_estado_v2`
- `exceles`
- `notebooklm`
- `.drive_snapshot.json`
- `.drive_watch_snapshot.json`
- `.metadata`

Los respaldos de corridas anteriores, archivos sueltos en la raíz, logs, bases temporales, dashboards, reportes y carpetas auxiliares deben eliminarse o mantenerse fuera de `FASP_WORK_DIR`. El código fuente del skill vive en este repositorio, no dentro de la carpeta local de datos.

## Flujo completo

```bash
export FASP_WORK_DIR="/ruta/a/FASP"
python3 scripts/etapa-0-sincronizar-completo
python3 scripts/etapa-1-renombrado
python3 scripts/etapa-2-extraccion-exceles
python3 scripts/etapa-3-integracion-corpusintegrado
python3 scripts/etapa-4-distribucion-por-estado
```

La etapa 2 genera cuatro archivos Excel: un corpus maestro y tres libros por categoría. Extrae páginas, metadatos PDF y un extracto de la primera página.

## Procesamiento por estado

```bash
python3 scripts/pipeline-por-estado "01 EdoMex Nancy G"
```

Las salidas se guardan bajo `corpusintegrado/<estado>/`, `exceles/<estado>/` y `corpus_por_estado_v2/<estado>/`. La carga a Drive no se ejecuta desde este comando para evitar conflictos entre ejecuciones concurrentes.

Durante el procesamiento se analiza el texto y los metadatos de cada PDF para obtener una etiqueta general a partir de su título o encabezado. Si Drive trae varios PDFs con el mismo nombre base pero contenido diferente, el pipeline conserva todos y genera nombres legibles para uso humano y NotebookLM, por ejemplo con una etiqueta breve de contenido y una versión visible (`V1.0`, `V1.1`, etc.). El SHA-256 queda en `contenido_manifest.json` para auditoría y trazabilidad, pero no aparece en el nombre final del archivo.

Para varios estados, sincroniza primero de manera secuencial y procesa después hasta tres estados en paralelo:

```bash
python3 scripts/orquestador-sincronizacion --run --workers 3
```

Para validar y aplicar en Drive los nombres finales generados en local:

```bash
python3 scripts/actualizar-nombres-drive-desde-manifest --dry-run
python3 scripts/actualizar-nombres-drive-desde-manifest
```

El resultado válido del último `--dry-run` después de aplicar cambios es `sin_cambios`. Si aparece `sin_file_id` o `file_id_no_resuelto`, la corrida debe considerarse bloqueada: el manifest perdió la relación con Drive y no debe aplicarse renombrado remoto.

También puede integrarse al cierre del orquestador:

```bash
python3 scripts/orquestador-sincronizacion --run --workers 3 --rename-drive
```

Para preparar carpetas locales de carga a NotebookLM Pro, genera un corpus por estado con bibliografía común, normativa federal común y normativa estatal:

```bash
python3 scripts/preparar-notebooklm-por-estado
```

La salida queda en `notebooklm/<estado>/` con:

- `00_Bibliografia`
- `01_Normativa_Federal`
- `02_Normativa_Estatal`
- `FUENTES_NOTEBOOKLM.md`
- `manifest_notebooklm.json`

Para publicar esa misma estructura como carpeta intermedia en Google Drive, sincroniza el corpus local hacia `FASP_NBLM`:

```bash
python3 scripts/sincronizar-notebooklm-drive --dry-run
python3 scripts/sincronizar-notebooklm-drive
```

Este paso crea o reutiliza `FASP_NBLM` en Mi unidad y replica las subcarpetas de `notebooklm/<estado>/`. La ejecución es incremental: cada archivo subido registra su SHA en Drive y se omite cuando el contenido local no cambió. Si el archivo existe pero cambió, se actualiza en el mismo `fileId`; no crea duplicados. No elimina archivos remotos por defecto.

## Garantías operativas

- La sincronización descarga archivos nuevos o modificados según su versión en Drive.
- Un choque de nombres normalizados conserva ambos PDFs; nunca elimina uno automáticamente.
- Los manifests conservan `drive_file_id`; no se depende del nombre visible para actualizar Drive.
- `sin_file_id` y `file_id_no_resuelto` son errores bloqueantes en el renombrado remoto.
- La integración rechaza nombres duplicados antes de modificar el corpus existente.
- La integración y distribución deduplican por SHA para evitar acumulación en corridas incrementales.
- El corpus NotebookLM se genera aparte de `corpusintegrado`; no modifica Drive ni crea notebooks automáticamente.
- `FASP_NBLM` es una carpeta intermedia en Drive para importar fuentes a NotebookLM; el pipeline puede actualizarla, pero la creación del notebook en NotebookLM Pro sigue siendo manual.
- La distribución se publica de forma completa y respalda la salida anterior, evitando PDFs obsoletos.
- El manifiesto del corpus registra origen, tamaño y SHA-256 de cada PDF.

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```
