# Plan: Sistema Multi-Agente Sativa Liquor

## Visión General

Sistema de agentes jerárquico donde el **CEO Agent (Sativa Boss)** orquesta agentes especializados por departamento, todos alimentados por una base de conocimiento construida sobre los documentos de `knowledge/`. El content engine (CMO + personas Dante/Valeria) es la prioridad de negocio por su impacto directo en cashflow.

---

## Arquitectura de Agentes

```
┌─────────────────────────────────────────┐
│           SATIVA BOSS (CEO)             │
│   Orquestador central · Estrategia      │
│   Decisiones finales · ROI              │
└────────┬──────────┬──────────┬──────────┘
         │          │          │
    ┌────▼───┐  ┌───▼────┐  ┌─▼──────┐
    │  CMO   │  │  CFO   │  │  COO   │
    │Content │  │Finanzas│  │  Ops   │
    └────┬───┘  └────────┘  └────────┘
         │
    ┌────▼──────────────┐
    │  Persona Engine    │
    │  Dante · Valeria   │
    └───────────────────┘
```

**Punto de entrada único:** Siempre se interactúa con el CEO. Él decide qué subagente activar. No se interactúa directamente con Dante/Valeria salvo en modo debug.

---

## Estructura del Proyecto

```
sativa-agents/
│
├── knowledge/                        # Base de conocimiento — voz, estrategia y operaciones
│   ├── brand/
│   │   ├── brand.md                  # ← migrado desde raíz
│   │   ├── avatars.md                # Dante y Valeria: PERSONALIDAD, voz, frases, restricciones
│   │   └── visual-codes.md           # Paleta, tipografía, estética detallada
│   ├── operations/
│   │   ├── menu.md                   # Productos, precios, promos activas
│   │   ├── logistics.md              # Domicilios: zonas, horarios, tarifas
│   │   └── suppliers.md              # Proveedores, costos de insumos
│   ├── finance/
│   │   ├── pricing-model.md          # Márgenes, ticket promedio, estructura de costos
│   │   └── weekly-targets.md         # North Star Metrics semanales
│   └── content/
│       ├── content-calendar.md       # Protocolo Sativa (Lun-Mié / Jueves / Finde)
│       └── published-content.md      # Archivo de contenido publicado y su performance
│
├── UGC/                              # Identidad visual generativa — archivos biométricos
│   ├── dante/
│   │   ├── face.md                   # Biometría facial: ángulos, expresiones, prompt maestro
│   │   └── body.md                   # Biometría corporal: proporciones, poses, prompts técnicos
│   └── valeria/
│       ├── face.md                   # Biometría facial: ángulos, expresiones, prompt maestro
│       └── body.md                   # Biometría corporal: proporciones, poses, prompts técnicos
│
│   NOTA: UGC/ no es knowledge general. Es la base de datos visual para generación de
│   imágenes con AI (Midjourney/SDXL). Los archivos son grandes (~10-14k tokens c/u)
│   y se acceden con RAG selectivo, no injection completa.
│
├── agents/                           # Definición de cada agente (system prompts)
│   ├── ceo/
│   │   ├── system-prompt.md          # Refactorizado desde CEO-borrador.md
│   │   └── tools.md                  # Lista de tools disponibles para el CEO
│   ├── cmo/
│   │   ├── system-prompt.md
│   │   └── tools.md
│   ├── cfo/
│   │   ├── system-prompt.md
│   │   └── tools.md
│   ├── coo/
│   │   ├── system-prompt.md
│   │   └── tools.md
│   └── personas/
│       ├── dante.md                  # Voz, personalidad, frases, restricciones (NO visual)
│       └── valeria.md                # Voz, personalidad, frases, restricciones (NO visual)
│
├── workflows/                        # Archivos YAML de configuración de procesos
│   ├── weekly-content.yaml           # Cómo el CMO ejecuta el plan de contenido semanal
│   ├── domicilio-response.yaml       # Flujo de atención por WhatsApp (manual → automático)
│   ├── financial-review.yaml         # Review semanal de caja que el CEO interpreta
│   └── sativa-sessions.yaml          # Workflow para eventos y DJ sets
│
├── src/                              # Código Python del sistema
│   ├── main.py                       # CLI entry point: `python main.py chat`
│   ├── config.py                     # Lee variables de .env, rutas, constantes
│   ├── knowledge_loader.py           # Fase 1: carga y concatena docs markdown para injection
│   ├── vector_store.py               # Fase 1 (UGC) / Fase 2 (knowledge): ChromaDB + embeddings
│   ├── agents/
│   │   ├── base_agent.py             # Clase base: llama a Claude API, maneja historial
│   │   ├── ceo.py
│   │   ├── cmo.py
│   │   ├── cfo.py
│   │   └── coo.py
│   ├── personas/
│   │   └── persona_engine.py         # Dos modos: "voice" (knowledge/) y "visual" (UGC/)
│   ├── memory/
│   │   └── session_store.py          # Persiste historial de sesiones en JSON (memory/)
│   └── tools/
│       ├── brand_retrieval.py        # Recupera contexto de brand/voz según query
│       ├── content_generator.py      # Genera captions, copies, briefs (texto)
│       ├── image_prompt_generator.py # Ensambla prompts para Midjourney/SDXL desde UGC/
│       └── financial_tracker.py      # Lee/escribe data/ CSVs para el CFO
│
├── data/                             # Datos operacionales (entrada manual hasta Fase 4)
│   ├── sales/
│   │   └── sales.csv                 # Ventas: fecha, producto, cantidad, total
│   ├── expenses/
│   │   └── expenses.csv              # Gastos: fecha, categoría, descripción, monto
│   └── README.md                     # Instrucciones para llenar los CSVs manualmente
│
├── memory/                           # Historial de sesiones persistido (JSON, no commitear)
│   └── .gitkeep
│
├── outputs/                          # Lo que generan los agentes
│   ├── content/                      # Posts y captions listos para publicar
│   ├── image-prompts/                # Prompts de imagen listos para Midjourney/SDXL
│   ├── reports/                      # Reportes financieros semanales
│   └── briefs/                       # Briefs creativos para el diseñador
│
├── .env.example                      # Template de variables de entorno
├── .gitignore
├── CLAUDE.md
├── PLAN.md                           # Este archivo
├── requirements.txt
│
│   [archivos legacy — migrar en Fase 1]
├── brand.md
└── CEO-borrador.md
```

---

## Los 5 Agentes Core

| Agente | Rol | Tools | Fuente de conocimiento |
|---|---|---|---|
| **CEO (Sativa Boss)** | Orquestador, estrategia, decisiones | Spawna subagentes, lee todos los docs | Todo `knowledge/` |
| **CMO** | Estrategia de contenido, calendario | content_generator, brand_retrieval | `brand/`, `content/` |
| **CFO** | Cashflow, márgenes, targets | financial_tracker (lee `data/` CSVs) | `finance/`, `data/` |
| **COO** | Operaciones, domicilios, inventario | logistics tools, draft WhatsApp | `operations/` |
| **Persona Engine** | Voz de marca + assets visuales (Dante ↔ Valeria) | brand_retrieval (voice), image_prompt_generator (visual) | `knowledge/brand/avatars.md` + `UGC/` |

### Dos modos del Persona Engine

```
persona_engine.py
├── modo "voice"   → lee agents/personas/{dante,valeria}.md + knowledge/brand/avatars.md
│                    OUTPUT: caption, copy, hilo narrativo en voz del personaje
└── modo "visual"  → RAG sobre UGC/{dante,valeria}/*.md
                     INPUT: descripción de la escena + ángulo + contexto
                     OUTPUT: prompt maestro para Midjourney/SDXL
```

El CMO decide qué modo activar según la tarea: si el brief del día es generar texto, activa `voice`; si es generar assets visuales, activa `visual`.

---

## Stack Tecnológico

```
Lenguaje:      Python 3.11+
LLM:           claude-opus-4-6 (orquestador CEO) / claude-sonnet-4-6 (subagentes)
SDK:           Anthropic Python SDK (nativo, sin abstracción extra)
Knowledge:     Fase 1 → file injection directo en system prompt (docs de knowledge/)
               Fase 1 → ChromaDB + RAG para UGC/ (archivos ~10-14k tokens, no inyectables completos)
               Fase 2 → ChromaDB extiende también a knowledge/ cuando el corpus lo justifique
Embeddings:    Voyage AI (recomendado por Anthropic, mejor retrieval para prompts visuales densos)
Memoria:       JSON files en memory/ (simple, sin base de datos)
Datos ops:     CSV files en data/ (entrada manual hasta Fase 4)
Workflows:     YAML config files leídos por los agentes
CLI:           argparse o Typer para `python main.py chat/run/report`
```

**Por qué no CrewAI/LangGraph:** El SDK nativo de Anthropic da control total del system prompt de cada agente, crítico para mantener el brand voice de Sativa. Se añade abstracción solo cuando el SDK nativo sea insuficiente.

**Por qué RAG entra en Fase 1 para UGC/:** Los archivos biométricos de Dante y Valeria pesan ~10-14k tokens cada uno. Inyectarlos completos en cada llamada es inviable en costo y contexto. El RAG recupera solo las secciones relevantes (ej: para un retrato solo recupera `face.md § prompt-maestro`; para full body recupera `body.md § ángulo-específico`).

---

## Fases de Implementación

### Fase 1 — Foundation (Knowledge Base + CEO) ✅ COMPLETA

**Objetivo:** Un CEO funcional que responde en character con contexto real de la marca. RAG activo para UGC/ desde el inicio.

1. ✅ Crear estructura de carpetas del proyecto
2. ✅ Configurar `.env.example`, `config.py`, `.gitignore`, `requirements.txt`
3. ✅ Migrar `brand.md` → `knowledge/brand/brand.md`
4. ✅ Expandir brand en documentos especializados: `avatars.md` (personalidad/voz), `visual-codes.md`
5. ✅ Crear documentos iniciales: `knowledge/content/content-calendar.md`, `knowledge/operations/menu.md`
6. ✅ Refactorizar `CEO-borrador.md` → `agents/ceo/system-prompt.md` (preservar el núcleo, estructurar con `<role>`, `<brand_rules>`, `<constraints>`, `<output_format>`)
7. ✅ Implementar `knowledge_loader.py`: carga y concatena docs markdown de `knowledge/` (file injection)
8. ✅ Implementar `vector_store.py`: ChromaDB indexando solo `UGC/` en esta fase, con retrieval selectivo por sección
9. ✅ Implementar `session_store.py`: persiste historial de sesiones en JSON
10. ✅ Implementar `base_agent.py`: llama Claude API, inyecta knowledge, mantiene historial
11. ✅ Implementar `ceo.py` y `main.py` con CLI básico (`python main.py chat`)

**Entregable:** `python main.py chat` → conversación con el Sativa Boss que conoce la marca y recuerda el historial entre sesiones.

---

### Fase 2 — CMO + Personas (Content Engine) ✅ COMPLETA

**Objetivo:** Generación automática de contenido semanal: texto (captions/copies) y prompts de imagen para assets visuales.

12. ✅ Implementar `persona_engine.py` con dos modos:
    - `voice`: recupera `agents/personas/{dante,valeria}.md` + `knowledge/brand/avatars.md`
    - `visual`: RAG sobre `UGC/{dante,valeria}/*.md` recuperando solo la sección relevante (facial vs full body vs ángulo específico)
13. ✅ Crear `agents/personas/dante.md` y `valeria.md` con prompt completo de **voz y personalidad** (frases tipo, restricciones, ejemplos on-brand)
14. ✅ Implementar `cmo.py`: lee `content-calendar.md`, decide qué modo del persona engine activar según tipo de tarea
15. ✅ Implementar `content_generator.py`: guarda caption + brief en `outputs/content/`
16. ✅ Implementar `image_prompt_generator.py`: persiste master prompt en `outputs/image-prompts/`
17. ✅ Inicializar `knowledge/content/published-content.md` para registrar posts publicados y su performance
18. ✅ Workflow `workflows/weekly-content.yaml`: define el proceso CMO → Persona(voice+visual) → creative brief → outputs
19. ✅ Añadir comando CLI: `python -m src.main run weekly-content [--date YYYY-MM-DD]`
20. ✅ Añadir comando CLI: `python -m src.main generate image --persona dante --scene "..." --angle "..." --framing portrait`

**Nuevos archivos creados en Fase 2:**
- `agents/personas/dante.md` — voz, protocolo Lun-Mié, restricciones, frases calibradoras
- `agents/personas/valeria.md` — voz, protocolo Vie-Dom, restricciones, frases calibradoras
- `agents/cmo/system-prompt.md` — CMO como estratega puro, output siempre JSON estructurado
- `src/personas/persona_engine.py` — servicio stateless con modos `voice` y `visual`
- `src/agents/cmo.py` — `generate_brief()` y `generate_creative_brief()`, no-streaming
- `src/tools/content_generator.py` — persistencia en `outputs/content/`
- `src/tools/image_prompt_generator.py` — persistencia en `outputs/image-prompts/`
- `src/workflows/runner.py` — ejecutor de workflows YAML con resolución de placeholders
- `workflows/weekly-content.yaml` — workflow de 4 pasos: brief → voice → visual → creative brief

**Cuando extender ChromaDB a knowledge/:** Si el corpus de `knowledge/` supera ~20 documentos y el file injection completo supera los límites útiles de contexto.

**Entregable:** `python -m src.main run weekly-content` → genera brief estratégico + caption en voz de Dante o Valeria + master prompt visual + creative brief integrado, todos persistidos en `outputs/`.

---

### Fase 3 — CFO básico (Financial Tracker)

**Objetivo:** Reportes semanales de salud financiera con recomendaciones del CEO.

21. Crear `data/sales/sales.csv` y `data/expenses/expenses.csv` con schema definido
22. Crear `data/README.md` con instrucciones claras para entrada manual de datos
23. Implementar `financial_tracker.py`: lee CSVs, calcula márgenes, ticket promedio, comparativo semana a semana
24. Implementar `cfo.py`: interpreta los datos y genera análisis en lenguaje de negocio
25. Workflow `workflows/financial-review.yaml`: define el reporte semanal automático
26. Añadir comando: `python main.py report financial`

**Entregable:** `python main.py report financial` → reporte de la semana con análisis del CFO y directivas del CEO.

---

### Fase 4a — COO + WhatsApp (Ops Engine)

**Nota:** La integración real con WhatsApp Business API requiere aprobación de Meta Business Manager (proceso de 2–4 semanas). El COO puede operar generando drafts de mensajes para envío manual mientras se gestiona la aprobación.

27. Implementar `coo.py`: gestiona lógica de domicilios, zonas, horarios, respuestas a clientes
28. Workflow `workflows/domicilio-response.yaml`: flujo de atención (recepción → confirmación → seguimiento)
29. Añadir comando: `python main.py chat --agent coo` para atender domicilios manualmente asistido por IA
30. Integrar WhatsApp API (Twilio o Meta) cuando esté aprobado

---

### Fase 4b — Instagram Integration

**Nota:** Instagram Graph API requiere cuenta Business verificada y revisión de permisos para posting automático.

31. Integración Instagram Graph API para scheduling de posts generados en Fase 2
32. Feedback loop: el CMO lee métricas de engagement para ajustar estrategia de contenido

---

## Decisiones de Diseño

| Decisión | Razón |
|---|---|
| **File injection en Fase 1** (no RAG) | El corpus actual no justifica vector DB. Más rápido de implementar y depurar. |
| **ChromaDB entra en Fase 2** | Cuando el corpus crezca y el injection completo exceda el contexto útil. |
| **`memory/` en JSON** | Persistencia simple, auditable, sin dependencias externas. |
| **`data/` en CSV** | El CFO necesita datos reales. CSV es lo más fácil de llenar manualmente. |
| **Persona Engine con dos modos (`voice`/`visual`)** | La voz y la imagen son pipelines diferentes. `voice` es texto; `visual` ensambla prompts para generadores de imagen. Mismo módulo, dos salidas. |
| **RAG en Fase 1 solo para `UGC/`** | Los archivos biométricos son 10-14k tokens cada uno — no inyectables completos. El knowledge general de `knowledge/` sigue con file injection hasta Fase 2. |
| **`UGC/` separado de `knowledge/`** | Son documentos de naturaleza distinta: `knowledge/` es texto estratégico/operacional; `UGC/` son bases de datos técnicas para generación visual. |
| **`agents/personas/` solo contiene voz** | La información visual vive en `UGC/`. Separar evita confusión y mantiene cada documento con un propósito único. |
| **`published-content.md` no `ugc-library.md`** | El nombre `ugc-library` colisionaba conceptualmente con la carpeta `UGC/`. |
| **`workflows/` como YAML** | Les da rol funcional (configuración que los agentes leen), no solo documental. |
| **Un modelo por jerarquía** | CEO usa `claude-opus-4-6`. Subagentes usan `claude-sonnet-4-6` para reducir costo. |
| **Human-in-the-loop hasta Fase 4** | Los agentes generan drafts, no publican solos. Todo pasa por aprobación antes de automatizar. |
| **Outputs estructurados en JSON** | Todos los agentes retornan `{content, rationale, brand_rules_applied}`. Auditables y mejorables. |

---

## Variables de Entorno (.env.example)

```env
# Anthropic
ANTHROPIC_API_KEY=

# Embeddings (Fase 2+)
VOYAGE_API_KEY=

# WhatsApp (Fase 4a)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=

# Paths
KNOWLEDGE_DIR=./knowledge
MEMORY_DIR=./memory
DATA_DIR=./data
OUTPUTS_DIR=./outputs
```

---

## Comandos CLI (main.py)

```bash
python main.py chat                                          # Conversación con el CEO (historial persistido)
python main.py chat --agent cmo                              # Modo debug: directo al CMO
python main.py chat --agent cfo                              # Modo debug: directo al CFO
python main.py chat --agent coo                              # Modo debug: directo al COO
python main.py run weekly-content                            # Genera plan de contenido semanal (texto)
python main.py run financial-review                          # Genera reporte financiero de la semana
python main.py report financial                              # Reporte CFO rápido
python main.py generate image \
  --persona dante \
  --scene "callejón urbano, atardecer dorado" \
  --angle "3/4 izquierdo" \
  --framing "full body"                                      # Prompt maestro para Midjourney/SDXL
python main.py memory clear                                  # Borra historial de sesión actual
```

---

## Migración de Archivos Legacy

| Archivo actual | Destino | Qué hacer |
|---|---|---|
| `brand.md` | `knowledge/brand/brand.md` | Mover. Expandir en `avatars.md` (solo voz/personalidad) y `visual-codes.md`. |
| `CEO-borrador.md` | `agents/ceo/system-prompt.md` | Refactorizar: preservar el núcleo de personalidad y reglas, estructurar con tags XML (`<role>`, `<brand_rules>`, `<constraints>`). |
| `UGC/dante/face.md` | `UGC/dante/face.md` | Ya en su lugar. Se indexa con ChromaDB en Fase 1. No mover. |
| `UGC/dante/body.md` | `UGC/dante/body.md` | Ya en su lugar. Se indexa con ChromaDB en Fase 1. No mover. |
| `UGC/valeria/face.md` | `UGC/valeria/face.md` | Ya en su lugar. Se indexa con ChromaDB en Fase 1. No mover. |
| `UGC/valeria/body.md` | `UGC/valeria/body.md` | Ya en su lugar. Se indexa con ChromaDB en Fase 1. No mover. |
