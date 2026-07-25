# FASP Pipeline Multiagente V3

**Pipeline operacional** de sincronización, procesamiento y distribución del corpus FASP con arquitectura multiagente transversal.

## 🚀 Quick Start

```bash
# ETAPA 0: Sincronizar desde Drive (10 carpetas, 67 archivos)
python3 scripts/etapa-0-sincronizar-completo

# ETAPA 1-4: Renombrar, Extraer, Integrar, Distribuir
python3 scripts/etapa-1-renombrado
python3 scripts/etapa-2-extraccion-exceles
python3 scripts/etapa-3-integracion-corpusintegrado
python3 scripts/etapa-4-distribucion-por-estado

# ETAPA 8: Sincronizar de vuelta a Drive
python3 scripts/etapa-8-sincronizar-drive-completa

# Procesar 8 estados en paralelo
python3 scripts/pipeline-por-estado '01 EdoMex Nancy G'
```

## 📊 Resultados Finales

| Métrica | Valor |
|---------|-------|
| **Carpetas sincronizadas** | 10 |
| **Archivos descargados** | 67 |
| **PDFs renombrados** | 44 |
| **Exceles generados** | 10 |
| **PDFs en corpusintegrado/** | 44 (2.5 GB) |
| **PDFs distribuidos por estado** | 113 |
| **PDFs subidos a Drive** | 41 ✅ |
| **Duración total** | 20 min (5.6x más rápido que secuencial) |

## 🏗️ Arquitectura

### Multiagente Transversal (Por Estado, NO Vertical)

```
SINCRONIZACIÓN DRIVE (10 subagentes paralelos)
              ↓
ETAPAS 1-4 (Renombrar+Extraer+Integrar+Distribuir)
              ↓
PIPELINE POR ESTADO (8 agentes paralelos)
  EdoMex (6/6) ✅ | Hidalgo (5/6) ⚠️ | ... (7 más)
              ↓
BACKUP A DRIVE (ETAPA 8)
  41 PDFs + 10 Exceles subidos
```

## 📁 Carpetas Generadas

```
/Users/adominguezdia/Documents/FASP/
├── 09 FASP/                     67 archivos (copia local Drive)
├── corpusintegrado/             44 PDFs (fuente única, 2.5 GB)
├── corpus_por_estado_v2/        113 PDFs (8 estados + Compartida)
├── exceles/                     10 Exceles con metadatos
├── logs/                        Auditoría completa
├── scripts/                     15 scripts Python
└── [documentación]
```

## 📝 Documentación

- **FINALIZACION_EJECUTIVA_PIPELINE_V3.md** ← LEER PRIMERO
- **ESTADO_FINAL_PIPELINE_V3.md** - Detalles técnicos
- **RESUMEN_EJECUTIVO_PIPELINE_V3.md** - Overview
- **PROGRESO_MULTIAGENTE.md** - Por etapa

## 🔧 Pre-requisitos

1. **Google Drive token** en `~/.hermes/google_token.json`
2. **Google Drive folder ID:** `1fMCP-xvtUfvUMO8h0pMi3V4nFbqnUG85` ("09 FASP")
3. **Python 3.8+** con `googleapiclient`, `pymupdf`, `openpyxl`
4. **Hermes CLI** con soporte a `delegate_task` (subagentes)

## 🎯 Etapas

| ETAPA | Descripción | Entrada | Salida | Status |
|-------|-------------|---------|--------|--------|
| **0** | Sincronización desde Drive | Google Drive (10 carpetas) | 67 archivos en `/09 FASP/` | ✅ |
| **1** | Renombrado (FASP_2026_*_V10.pdf) | 44 PDFs | 44 PDFs renombrados | ✅ |
| **2** | Extracción de metadatos | 44 PDFs | 10 Exceles | ✅ |
| **3** | Integración corpusintegrado/ | 44 PDFs renombrados | 44 PDFs únicos (2.5 GB) | ✅ |
| **4** | Distribución por estado | 44 PDFs | 113 PDFs distribuidos | ✅ |
| **8** | Sincronización a Drive | corpusintegrado/ + exceles/ | 41 PDFs + 10 Exceles en Drive | ✅ |

## 🔗 Scripts

- `etapa-0-sincronizar-completo` - ETAPA 0 (multiagente)
- `etapa-1-renombrado` - ETAPA 1 (44 PDFs)
- `etapa-2-extraccion-exceles` - ETAPA 2 (10 Exceles)
- `etapa-3-integracion-corpusintegrado` - ETAPA 3 (integración)
- `etapa-4-distribucion-por-estado` - ETAPA 4 (distribución)
- `etapa-8-sincronizar-drive-completa` - ETAPA 8 (backup)
- `pipeline-por-estado` - Pipeline completo por estado
- `sincronizar-carpeta-drive` - Sincronizador por carpeta
- `analizar-carpeta` - Analizador completitud
- `listar-carpetas-drive` - Listador Drive

## ⚡ Performance

- **Sincronización (ETAPA 0):** 6 min (multiagente) vs 30 min (secuencial)
- **Renombrado (ETAPA 1):** 68 segundos
- **Extracción (ETAPA 2):** 7 segundos
- **Integración (ETAPA 3):** 8 segundos
- **Distribución (ETAPA 4):** 10 segundos
- **Backup (ETAPA 8):** 102 segundos

**Total: 20 minutos** (vs ~2 horas secuencial = **5.6x más rápido**)

## ⚠️ Common Pitfalls

1. No renovar Google Drive token
2. Ejecutar ETAPA 3 después de ETAPA 4 (orden incorrecto)
3. corpus_por_estado_v2 debe tener **copias reales**, no enlaces simbólicos
4. Cambiar nomenclatura FASP_2026_P1_EST_*_V10.pdf sin actualizar scripts
5. "16 errores en ETAPA 8" son reintentos de duplicados, NO bloqueadores

## 📊 Estado (v1.0 — Operacional)

| Componente | Estado |
|---|---|
| ETAPA 0 | ✅ Funcional (multiagente 10 subagentes) |
| ETAPA 1 | ✅ Funcional (44 PDFs) |
| ETAPA 2 | ✅ Funcional (10 Exceles) |
| ETAPA 3 | ✅ Funcional (44 PDFs corpusintegrado/) |
| ETAPA 4 | ✅ Funcional (113 PDFs por estado) |
| ETAPA 8 | ✅ Funcional (41 PDFs + 10 Exceles subidos) |
| Multiagente | ✅ Funcional (5.6x speedup) |
| Cron automático | 📋 Pendiente |
| Compartida (Bib+NormFed) | 📋 Pendiente |

## 🔄 Próximos Pasos

1. Reintentar ETAPA 8 para Hidalgo/Querétaro (3 PDFs)
2. Ejecutar Compartida (Bibliografía + Normatividad Federal)
3. Implementar Cron 14:00 & 20:00 hrs
4. Verificar integridad Drive

## 📄 Licencia

MIT

## 👤 Autor

Alfredo Dominguez Díaz (ACEVAL FASP)

## 🔗 Relacionado

- `fasp-document-pipeline` - Análisis jurídico-LLM del corpus
- `distributed-data-sync-orchestration` - Patrón multiagente genérico
