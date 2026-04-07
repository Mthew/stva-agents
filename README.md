# Sativa Agents

Sistema multi-agente de IA para gestionar **Sativa Liquor** — un bar de granizados con licor en Altavista, Medellín. El sistema incluye un CEO Agent orquestador y subagentes especializados por área de la empresa (CMO, CFO, COO), todos alimentados por una base de conocimiento de la marca.

---

## Conceptos de Python si vienes de TypeScript / .NET

Antes del setup, acá van los equivalentes directos para que el código no se sienta extraño:

| TypeScript / .NET | Python | Notas |
|---|---|---|
| `package.json` | `requirements.txt` | Lista de dependencias del proyecto |
| `npm install` | `pip install -r requirements.txt` | Instala todas las dependencias |
| `npm run dev` | `python -m src.main chat` | Corre el proyecto |
| `node_modules/` | Instalación global del sistema | Python instala paquetes globalmente (o en un venv) |
| `interface` / `abstract class` | `class` con métodos sin implementar | Python no tiene interfaces nativas |
| `.env` | `.env` | Igual — variables de entorno |
| `import { X } from './module'` | `from src.module import X` | Misma idea, diferente sintaxis |
| `async/await` | `async/await` | Idéntico en concepto |
| `console.log()` | `print()` | |
| `any[]` / `List<T>` | `list[dict]` | Python usa type hints opcionales |
| `Record<string, any>` | `dict` | Diccionario clave-valor |
| `null` | `None` | |

**Un detalle importante de Python:** no hay llaves `{}` para delimitar bloques — usa indentación. 4 espacios = un nivel de anidación.

---

## Prerequisitos

- **Python 3.11 o superior** — verificar con `python3 --version`
- **Una API Key de Anthropic** — obtenerla en [console.anthropic.com](https://console.anthropic.com)

### ¿Cómo sé qué versión tengo?

```bash
python3 --version
# Python 3.14.3  ← cualquier 3.11+ sirve
```

---

## Setup (primera vez)

### 1. Instalar dependencias

```bash
# Equivalente a `npm install`
python3 -m pip install -r requirements.txt
```

Esto instala:
- `anthropic` — SDK oficial de Claude (equivalente a `@anthropic-ai/sdk` en npm)
- `chromadb` — base de datos vectorial local para búsqueda semántica
- `python-dotenv` — lee el archivo `.env` (como `dotenv` en Node)
- `typer` — framework de CLI (como `commander` en Node)
- `rich` — texto con colores y formato en la terminal

### 2. Configurar variables de entorno

```bash
# Copiar el template
cp .env.example .env
```

Abrir `.env` y poner la API Key:

```env
ANTHROPIC_API_KEY=sk-ant-...tu-key-aquí...
```

### 3. Indexar los archivos de personajes (primera vez)

Los archivos biométricos de Dante y Valeria en `UGC/` son demasiado grandes para cargarlos completos — se indexan en una base de datos local para búsqueda inteligente. Solo hace falta correr esto una vez:

```bash
python -m src.main index
```

### 4. Hablar con el CEO

```bash
python -m src.main chat
```

### 5. Generar contenido de la semana

```bash
python -m src.main run weekly-content
```

El sistema detecta el día de hoy automáticamente y asigna el personaje correcto (Dante Lun-Mié, voz institucional Jue, Valeria Vie-Dom). Genera tres archivos en `outputs/`:
- `outputs/content/` — caption + hashtags listo para publicar
- `outputs/image-prompts/` — master prompt para Midjourney/SDXL
- `outputs/briefs/` — brief creativo integrado para revisión humana

---

## Estructura del Proyecto

```
sativa-agents/
│
├── knowledge/              # Base de conocimiento — archivos markdown que los agentes leen
│   ├── brand/              # Identidad de marca: brand.md, avatars.md, visual-codes.md
│   ├── content/            # Protocolo de contenido semanal, historial de posts publicados
│   ├── finance/            # Modelo de precios, targets semanales
│   └── operations/         # Menú, logística de domicilios, proveedores
│
├── UGC/                    # Archivos biométricos de Dante y Valeria
│   ├── dante/
│   │   ├── face.md         # Biometría facial + prompts para generar retratos con AI
│   │   ├── body.md         # Proporciones corporales + prompts full body
│   │   └── assets/         # Imágenes generadas de referencia
│   └── valeria/            # Misma estructura
│
├── agents/                 # Definición de cada agente (system prompts en markdown)
│   ├── ceo/
│   │   ├── system-prompt.md    # Instrucciones base del CEO (Sativa Boss)
│   │   └── tools.md            # Lista de tools disponibles por fase
│   ├── cmo/
│   │   └── system-prompt.md    # CMO: estratega de contenido, output siempre JSON
│   ├── cfo/                # Pendiente — Fase 3
│   ├── coo/                # Pendiente — Fase 4
│   └── personas/
│       ├── dante.md        # Voz de Dante: reglas, protocolo Lun-Mié, restricciones
│       └── valeria.md      # Voz de Valeria: reglas, protocolo Vie-Dom, restricciones
│
├── workflows/              # Archivos YAML que definen procesos automatizados
│   ├── weekly-content.yaml     # Generación del plan de contenido diario/semanal
│   └── financial-review.yaml   # Pendiente — Fase 3
│
├── src/                    # Código Python — el motor del sistema
│   ├── main.py             # Entry point del CLI (equivalente a index.ts)
│   ├── config.py           # Lee .env y define rutas (equivalente a config.ts)
│   ├── knowledge_loader.py # Lee y concatena los markdown de knowledge/
│   ├── vector_store.py     # ChromaDB: indexa UGC/ y hace búsquedas semánticas
│   ├── agents/
│   │   ├── base_agent.py   # Clase base: llama a Claude API, maneja historial
│   │   ├── ceo.py          # CEO Agent (claude-opus-4-6)
│   │   ├── cmo.py          # CMO Agent: generate_brief() y generate_creative_brief()
│   │   └── ...             # CFO, COO — Fases 3, 4
│   ├── memory/
│   │   └── session_store.py  # Guarda y carga historial de conversaciones en JSON
│   ├── personas/
│   │   └── persona_engine.py # Modos voice (caption) y visual (Midjourney prompt)
│   ├── tools/
│   │   ├── content_generator.py      # Persiste captions en outputs/content/
│   │   └── image_prompt_generator.py # Persiste master prompts en outputs/image-prompts/
│   └── workflows/
│       └── runner.py       # Ejecutor de workflows YAML con resolución de placeholders
│
├── data/                   # Datos operacionales (entrada manual)
│   ├── sales/sales.csv     # Registro de ventas: fecha, producto, cantidad, total
│   └── expenses/expenses.csv  # Registro de gastos: fecha, categoría, monto
│
├── memory/                 # Historial de conversaciones guardado (archivos JSON)
│   └── default.json        # Se crea automáticamente al usar `chat`
│
├── outputs/                # Lo que generan los agentes
│   ├── content/            # Captions y posts listos para publicar
│   ├── image-prompts/      # Prompts para Midjourney/SDXL
│   ├── reports/            # Reportes financieros semanales
│   └── briefs/             # Briefs creativos para el diseñador
│
├── .env                    # Variables de entorno — NO commitear
├── .env.example            # Template de variables (sí se commitea)
├── .gitignore
├── requirements.txt        # Dependencias (equivalente a package.json)
├── PLAN.md                 # Plan detallado de implementación por fases
└── CLAUDE.md               # Instrucciones para Claude Code (IA del repo)
```

---

## Cómo funciona el sistema

### Flujo de una conversación

```
tú escribes algo
    ↓
main.py recibe el input
    ↓
CEOAgent carga:
  • system prompt de agents/ceo/system-prompt.md
  • todos los docs de knowledge/ (inyectados directo al prompt)
  • historial previo de memory/default.json
    ↓
Llama a Claude API (claude-opus-4-6) con todo ese contexto
    ↓
Respuesta en streaming → se imprime en tiempo real
    ↓
Guarda user + respuesta en memory/default.json
```

### Por qué hay dos sistemas de knowledge

Los docs de `knowledge/` son cortos (texto de marca, operaciones, finanzas) y se inyectan completos en el prompt — como pasar un string largo al contexto de un LLM.

Los archivos de `UGC/` son enormes (~14,000 tokens cada uno) — no caben en el prompt. Se guardan en **ChromaDB** (una base de datos local que vive en `.chroma/`) y se recuperan solo los fragmentos relevantes según la pregunta. Esto es RAG (Retrieval-Augmented Generation).

### Jerarquía de agentes

```
CEO (claude-opus-4-6)         ← orquestador, conversación interactiva
├── CMO (claude-sonnet-4-6)   ← genera briefs estratégicos + creative briefs
│       └── Persona Engine    ← Dante (voz Lun-Mié) / Valeria (voz Vie-Dom)
│               ├── modo voice  → caption en voz del personaje
│               └── modo visual → master prompt para Midjourney/SDXL (RAG UGC/)
├── CFO (claude-sonnet-4-6)   ← finanzas                     [Fase 3]
└── COO (claude-sonnet-4-6)   ← operaciones                  [Fase 4]
```

El CEO usa el modelo más potente porque toma decisiones. Los subagentes usan Sonnet (más barato, más rápido) porque ejecutan tareas concretas.

---

## Comandos disponibles

```bash
# ── CEO — conversación interactiva ───────────────────────────────────────────

# Conversación con el CEO
python -m src.main chat

# Conversación en sesión nombrada (para separar contextos)
python -m src.main chat --session nombre-sesion

# Empezar sin cargar historial previo
python -m src.main chat --no-history

# ── Content Engine (Fase 2) ───────────────────────────────────────────────────

# Generar el contenido del día (brief + caption + prompt visual + creative brief)
python -m src.main run weekly-content

# Generar contenido para una fecha específica
python -m src.main run weekly-content --date 2026-04-11

# Generar solo el master prompt de imagen para Midjourney/SDXL
python -m src.main generate image --persona dante --scene "callejón, atardecer" --angle "3/4" --framing portrait
python -m src.main generate image --persona valeria --scene "neón y lluvia" --angle "frontal" --framing full_body

# ── Memoria y ChromaDB ────────────────────────────────────────────────────────

# Ver sesiones guardadas
python -m src.main memory list

# Borrar historial de la sesión actual
python -m src.main memory clear

# Borrar historial de una sesión específica
python -m src.main memory clear --session nombre-sesion

# Re-indexar UGC/ en ChromaDB (necesario si se editan los archivos de Dante/Valeria)
python -m src.main index

# Forzar re-indexado completo
python -m src.main index --force
```

---

## FAQ para devs de TypeScript / .NET

**¿Por qué `python -m src.main` y no solo `python src/main.py`?**
El flag `-m` le dice a Python que ejecute el módulo `src.main` dentro del paquete `src`, lo que hace que los imports relativos (`from src.config import ...`) funcionen correctamente. Es el equivalente a tener el working directory configurado en el runner de TypeScript.

**¿Qué es un `.venv`?**
Un entorno virtual — como tener `node_modules/` local al proyecto en lugar de global. En este proyecto no se usa por simplicidad, pero si ves conflictos de versiones entre proyectos, ejecuta:
```bash
python3 -m venv .venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows
python3 -m pip install -r requirements.txt
```

**¿Por qué los archivos de agentes son markdown y no código?**
El system prompt de cada agente es texto — no tiene sentido hardcodearlo en Python. Guardarlo en markdown permite editarlo sin tocar código, versionarlo en git con diffs legibles y reutilizarlo fuera del sistema (ej: copiar el prompt directo en Claude.ai).

**¿Cómo agrego datos de ventas?**
Abrir `data/sales/sales.csv` y añadir filas manualmente. El formato está documentado en `data/README.md`. En Fase 3, el CFO Agent leerá este archivo para generar reportes.

---

## Estado actual del proyecto

| Fase | Descripción | Estado |
|---|---|---|
| **Fase 1** | CEO Agent + knowledge base + sesiones persistidas | ✅ Completo |
| **Fase 2** | CMO + Persona Engine (Dante/Valeria) — content engine | ✅ Completo |
| **Fase 3** | CFO + reportes financieros desde CSV | Pendiente |
| **Fase 4a** | COO + integración WhatsApp | Pendiente |
| **Fase 4b** | Integración Instagram Graph API | Pendiente |

### Qué genera el sistema hoy (Fases 1 + 2)

Ejecutar `python -m src.main run weekly-content` produce automáticamente:

1. **Brief estratégico** — el CMO decide personaje, formato, tema y objetivos según el día
2. **Caption listo para publicar** — en la voz exacta de Dante o Valeria según el protocolo
3. **Master prompt de imagen** — listo para pegar en Midjourney o SDXL, con contexto biométrico real del personaje
4. **Creative brief integrado** — paquete completo para revisión humana antes de publicar

Todo en `outputs/` con `status: "pending_review"` — nada se publica automáticamente.
