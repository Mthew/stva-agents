# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

Sistema multi-agente de IA para gestionar **Sativa Liquor** — un bar de granizados con licor ubicado en Altavista, Medellín, Colombia. El sistema incluye un CEO Agent orquestador y subagentes especializados (CMO, CFO, COO) alimentados por una base de conocimiento de marca.

## Commands

```bash
# Instalar dependencias
python3 -m pip install -r requirements.txt

# Conversar con el CEO Agent
python -m src.main chat

# Conversar en sesión nombrada
python -m src.main chat --session nombre-sesion

# Ver sesiones guardadas
python -m src.main memory list

# Borrar historial de sesión
python -m src.main memory clear

# Re-indexar archivos UGC/ en ChromaDB
python -m src.main index --force
```

## Architecture

### Agent Hierarchy
```
CEO (claude-opus-4-6)        ← único punto de entrada
├── CMO (claude-sonnet-4-6)  ← contenido, calendario, personas
├── CFO (claude-sonnet-4-6)  ← finanzas, márgenes, reportes
└── COO (claude-sonnet-4-6)  ← operaciones, domicilios
        └── Persona Engine   ← Dante (voz) / Valeria (voz + visual)
```

### Knowledge Pipeline
- `knowledge/` — documentos markdown inyectados directamente en el system prompt (file injection)
- `UGC/` — archivos biométricos grandes (~10-14k tokens c/u), accedidos via RAG con ChromaDB
- `agents/*/system-prompt.md` — definición de cada agente con tags XML estructurados
- `memory/*.json` — historial de sesiones persistido entre ejecuciones

### Key Files
| File | Purpose |
|---|---|
| `src/agents/ceo.py` | CEO Agent — construye system prompt inyectando todo `knowledge/` |
| `src/agents/base_agent.py` | Clase base con streaming, historial y llamada a Claude API |
| `src/knowledge_loader.py` | File injection: carga y concatena docs de `knowledge/` por sección |
| `src/vector_store.py` | ChromaDB para UGC/: indexa chunks por `persona` + `file_type` |
| `src/memory/session_store.py` | JSON persistence del historial de conversaciones |
| `src/main.py` | CLI entry point con Typer + Rich |

### Data Flow

```
Usuario → main.py chat
  → CEOAgent.chat(message)
    → knowledge_loader.load_all_knowledge()  [inyectado en system prompt]
    → session_store.load_session()           [historial previo]
    → anthropic.messages.stream()            [claude-opus-4-6]
    → session_store.append_message()         [persiste respuesta]
```

### UGC Structure
`UGC/dante/` y `UGC/valeria/` contienen archivos biométricos para generación de imágenes con AI:
- `face.md` — biometría facial, ángulos, expresiones, prompt maestro para retratos
- `body.md` — proporciones corporales, poses, prompts técnicos full body
- `assets/` — imágenes generadas de referencia (no commitear nuevas sin aprobación)

El `vector_store.py` indexa estos archivos en ChromaDB con metadata `{persona, file_type}` para retrieval selectivo.

### Environment
Requiere `.env` con `ANTHROPIC_API_KEY`. Ver `.env.example` para todas las variables.
`VOYAGE_API_KEY` es opcional en Fase 1 — ChromaDB usa embeddings por defecto (all-MiniLM-L6-v2).

## Implementation Phases

- **Fase 1 (completa):** CEO Agent funcional con knowledge base y sesiones persistidas
- **Fase 2 (siguiente):** CMO + Persona Engine (Dante/Valeria) — content engine y generación de image prompts
- **Fase 3:** CFO con CSV financiero y reportes semanales
- **Fase 4a/4b:** COO + integraciones WhatsApp/Instagram

## Brand Context (crítico para todos los agentes)

- **Regla de oro:** "Más alcohol, menos confiticos" — nunca estética infantil o kawaii
- **El local:** "El Portal" / "El Bunker" en Altavista — no es un bar, es un portal de desconexión
- **Dante:** La Mente — voz filosófica, cínica, contundente. Contenido Lun-Mié
- **Valeria:** El Cuerpo — hedonista, sensorial, FOMO. Contenido Vie-Dom
- **No mencionar:** hoja de marihuana explícita — evocar el efecto, no el ingrediente
