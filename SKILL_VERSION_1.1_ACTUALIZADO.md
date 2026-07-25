# FASP Pipeline Multiagente V3 - Versión 1.1 Actualizada

## Versión 1.1 (2026-07-24 22:30)

**Nueva funcionalidad:** Análisis de múltiples versiones de archivos con mismo nombre

### Cambios principales:

1. **Descarga y análisis de TODAS las versiones** de cada archivo (no solo la primera)
2. **Identificación automática de decretos** (DECRETO NÚMERO 360, 85, 182, 207, 83)
3. **Análisis de contenido PDF** para determinar tipo de documento
4. **Búsqueda recursiva en subcarpetas** (ETAPA 0 mejorada)

### Estadísticas actualizadas:

| Métrica | v1.0 | v1.1 |
|---------|------|------|
| PDFs analizados | 44 | 71 |
| Estados cubiertos | 8 | 10 |
| Versiones detectadas | — | 16 (duplicados de contenido) |
| Decretos identificados | — | 5 automáticamente |
| Scripts nuevos | — | `descargar-y-analizar-todos-estados` |

### Distribución por estado (v1.1):

- EdoMex: 23 PDFs + 12 versiones = 35 total
- Querétaro: 8 PDFs + 3 versiones = 11 total
- Hidalgo: 5 PDFs + 1 versión = 6 total
- Bibliografía: 15 PDFs (sin duplicados)
- Coordinación: 15 PDFs (sin duplicados)
- Otros 5 estados: 1 PDF c/u (sin duplicados)

**Total:** 71 PDFs únicos descargados, 16 versiones adicionales analizadas

### Nuevos scripts:

1. `descargar-y-analizar-todos-pdfs` — EdoMex individual
2. `descargar-y-analizar-todos-estados` — 10 estados en paralelo

### Status: ✅ Verificación en curso (Git v1.1 actualizado)

