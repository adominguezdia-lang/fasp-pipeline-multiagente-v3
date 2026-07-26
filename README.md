# FASP Pipeline Multiagente V4

Pipeline para sincronizar, normalizar, analizar y distribuir documentos FASP.

## Estado

V4 es la versión operativa vigente. El pipeline está preparado para ejecuciones reproducibles e incrementales. Cada estado se procesa en sus propias salidas; la publicación en Drive se ejecuta como operaciones separadas y trazables.

El flujo es incremental: puede correrse durante varios días sobre la misma carpeta. Los archivos ya versionados se reconocen por su SHA y por `drive_file_id` en `contenido_manifest.json`; no deben re-versionarse como documentos nuevos.

El comando histórico `scripts/etapa-8-sincronizar-drive` está obsoleto en V4. No debe usarse para publicar PDFs, Exceles ni corpus NotebookLM, porque no respeta el flujo actual basado en manifest, `fileId` y SHA.

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

La etapa 2 genera cuatro archivos Excel: un inventario maestro y tres libros por categoría. Incluye documentos PDF y hojas de cálculo cargadas en Drive. Para PDFs extrae páginas, metadatos, título legible, fuente del título, estado de texto extraíble, extracto y SHA-256. Cuando el PDF no trae título interno, se infiere desde el texto o desde el nombre del archivo y se registra en `Fuente Titulo`. La columna `Ruta Drive` registra la ruta original en Drive, y `Ruta Local` queda solo como trazabilidad operativa. Cuando se ejecuta por estado, el Excel incluye bibliografía común, normativa federal común y documentos estatales del usuario para que coincida con las fuentes preparadas para NotebookLM.

## Procesamiento por estado

```bash
python3 scripts/pipeline-por-estado "01 EdoMex Nancy G"
```

Las salidas se guardan bajo `corpusintegrado/<estado>/`, `exceles/<estado>/` y `corpus_por_estado_v2/<estado>/`. La carga a Drive no se ejecuta desde este comando para evitar conflictos entre ejecuciones concurrentes.

Durante el procesamiento se analiza el texto y los metadatos de cada PDF para obtener una etiqueta general a partir de su título o encabezado. Si Drive trae varios PDFs con el mismo nombre base pero contenido diferente, el pipeline conserva todos y genera nombres legibles para uso humano y NotebookLM, por ejemplo con una etiqueta breve de contenido y una versión visible (`V1.0`, `V1.1`, etc.). El SHA-256 queda en `contenido_manifest.json` para auditoría y trazabilidad, pero no aparece en el nombre final del archivo.

Para publicar o actualizar en Drive los Exceles generados, usa una carpeta estable `FASP_EXCELES`:

```bash
python3 scripts/sincronizar-exceles-drive --dry-run
python3 scripts/sincronizar-exceles-drive
```

Este paso es incremental: conserva la estructura `exceles/<estado>/`, actualiza archivos existentes cuando cambia su SHA y omite archivos sin cambios. No borra archivos remotos por defecto.

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

## Recuperación de un estado incompleto

Si una carpeta de estado en Drive conserva archivos sin renombrar o el Excel muestra menos documentos que Drive, no ejecutes `etapa-8`. Rebaselinea solo ese estado desde Drive y conserva la trazabilidad por `fileId`:

```bash
python3 scripts/sincronizar-carpeta-drive "07 Tamaulipas Jackie"
python3 scripts/analizar-y-versionar-pdfs --source "$FASP_WORK_DIR/09 FASP/07 Tamaulipas Jackie"
python3 scripts/actualizar-nombres-drive-desde-manifest --source "$FASP_WORK_DIR/09 FASP/07 Tamaulipas Jackie" --dry-run
python3 scripts/actualizar-nombres-drive-desde-manifest --source "$FASP_WORK_DIR/09 FASP/07 Tamaulipas Jackie"
python3 scripts/etapa-2-extraccion-exceles --source "$FASP_WORK_DIR/09 FASP/07 Tamaulipas Jackie"
python3 scripts/sincronizar-exceles-drive --dry-run
python3 scripts/sincronizar-exceles-drive
```

El `--dry-run` de renombrado debe terminar con `sin_cambios` después de aplicar. Si aparecen `sin_file_id` o `file_id_no_resuelto`, detén la actualización: el manifest no puede relacionar el archivo local con Drive.

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

Además genera una carpeta de novedades por corrida en `FASP_NBLM_NOVEDADES/<fecha_hora>/`, por ejemplo `FASP_NBLM_NOVEDADES/2026-07-25_211500/`. Esa carpeta se crea en cada ejecución real y contiene solo archivos nuevos o modificados, preservando la ruta por estado y sección. En NotebookLM, después de la primera carga completa, usa esta carpeta de novedades para agregar fuentes sin tener que seleccionar manualmente entre todo el corpus. Si no hay archivos nuevos o modificados, la carpeta de ejecución queda vacía y sirve como evidencia de que no hubo novedades.

Si se requiere una etiqueta específica para la corrida:

```bash
python3 scripts/sincronizar-notebooklm-drive --run-label 2026-07-25_211500
```

## Garantías operativas

- La sincronización descarga archivos nuevos o modificados según su versión en Drive.
- La publicación remota de V4 usa `actualizar-nombres-drive-desde-manifest`, `sincronizar-exceles-drive` y `sincronizar-notebooklm-drive`; `etapa-8` queda bloqueada por obsoleta.
- Un choque de nombres normalizados conserva ambos PDFs; nunca elimina uno automáticamente.
- Los manifests conservan `drive_file_id`; no se depende del nombre visible para actualizar Drive.
- `sin_file_id` y `file_id_no_resuelto` son errores bloqueantes en el renombrado remoto.
- La integración rechaza nombres duplicados antes de modificar el corpus existente.
- La integración y distribución deduplican por SHA para evitar acumulación en corridas incrementales.
- El corpus NotebookLM se genera aparte de `corpusintegrado`; no modifica Drive ni crea notebooks automáticamente.
- `FASP_NBLM` es una carpeta intermedia en Drive para importar fuentes a NotebookLM; el pipeline puede actualizarla, pero la creación del notebook en NotebookLM Pro sigue siendo manual.
- `FASP_NBLM_NOVEDADES/<fecha_hora>` se crea en cada ejecución real y contiene únicamente fuentes nuevas o modificadas para agregarlas manualmente al notebook sin revisar todo el corpus.
- `FASP_EXCELES` es la carpeta estable en Drive para publicar los libros generados; se actualiza por SHA y evita duplicados.
- La distribución se publica de forma completa y respalda la salida anterior, evitando PDFs obsoletos.
- El manifiesto del corpus registra origen, tamaño y SHA-256 de cada PDF.

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```
