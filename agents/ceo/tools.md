# Tools disponibles para el CEO Agent

## Fase 1 (implementadas)

| Tool | Función | Cuándo usarla |
|---|---|---|
| `get_brand_context(query)` | Recupera docs relevantes de `knowledge/` para el query | Siempre que el CEO necesite contexto de marca antes de responder |
| `get_session_history()` | Carga historial de conversación de la sesión actual | Al inicio de cada sesión para mantener continuidad |
| `save_to_memory(content, key)` | Persiste información importante en la sesión JSON | Cuando el usuario comparte datos de ventas, decisiones o contexto nuevo |

## Fase 2 (se añaden con el CMO)

| Tool | Función |
|---|---|
| `generate_content(persona, type, context)` | Genera caption/copy en voz de Dante o Valeria |
| `generate_image_prompt(persona, scene, angle, framing)` | Ensambla prompt maestro para Midjourney/SDXL desde UGC/ |
| `run_weekly_content_workflow()` | Ejecuta el flujo completo de contenido semanal |

## Fase 3 (se añaden con el CFO)

| Tool | Función |
|---|---|
| `get_financial_summary(period)` | Lee CSVs de `data/` y calcula métricas financieras |
| `generate_financial_report()` | Genera reporte semanal de salud financiera |
