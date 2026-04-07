"""
content_generator.py — Tool de generación y persistencia de contenido

Recibe outputs del CMO + Persona Engine (modo voice) y produce el
paquete de contenido final guardado en outputs/content/.

Stateless — no llama a Claude. Toda la inteligencia viene de los agentes.
"""

import json
import re
from datetime import date as date_type
from pathlib import Path

from src.config import OUTPUTS_DIR


def save_content_output(
    cmo_brief: dict,
    persona_output: dict,
    target_date: str,
) -> Path:
    """
    Combina CMO brief + Persona voice output y guarda en outputs/content/.

    Args:
        cmo_brief:      dict del CMO (generate_brief output)
        persona_output: dict del PersonaEngine.generate_voice output
        target_date:    fecha en formato "YYYY-MM-DD"

    Returns:
        Path del archivo guardado
    """
    brief_content = cmo_brief.get("content", cmo_brief)
    voice_content = persona_output.get("content", {})

    persona = brief_content.get("persona", "unknown")
    content_type = brief_content.get("content_type", "post")

    package = {
        "date": target_date,
        "persona": persona,
        "content_type": content_type,
        "caption": voice_content.get("caption", ""),
        "hashtags": voice_content.get("hashtags", []),
        "visual_note": voice_content.get("visual_note", ""),
        "rationale": persona_output.get("rationale", ""),
        "brand_rules_applied": persona_output.get("brand_rules_applied", []),
        "cmo_brief": brief_content,
        "status": "draft",
    }

    output_path = _build_output_path(OUTPUTS_DIR / "content", target_date, persona, content_type)
    _write_json(package, output_path)
    return output_path


def _build_output_path(
    directory: Path,
    target_date: str,
    persona: str,
    content_type: str,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{target_date}_{persona}_{content_type}.json"
    return directory / filename


def _write_json(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
