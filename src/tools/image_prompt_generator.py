"""
image_prompt_generator.py — Tool de persistencia de prompts de imagen

Recibe el output de PersonaEngine.generate_visual() y lo guarda en
outputs/image-prompts/ con metadata completa.

Stateless — no llama a Claude. La generación del prompt ocurre en PersonaEngine.
"""

import json
import re
from pathlib import Path

from src.config import OUTPUTS_DIR


def save_image_prompt(
    visual_output: dict,
    persona: str,
    scene: str,
    target_date: str,
) -> Path:
    """
    Guarda el output de PersonaEngine.generate_visual() en outputs/image-prompts/.

    Args:
        visual_output: dict del PersonaEngine.generate_visual output
        persona:       "dante" | "valeria"
        scene:         descripción de la escena (se slugifica para el nombre del archivo)
        target_date:   fecha en formato "YYYY-MM-DD"

    Returns:
        Path del archivo guardado
    """
    visual_content = visual_output.get("content", {})

    package = {
        "date": target_date,
        "persona": persona,
        "scene": scene,
        "angle": visual_content.get("angle", ""),
        "framing": visual_content.get("framing", ""),
        "master_prompt": visual_content.get("master_prompt", ""),
        "negative_prompt": visual_content.get("negative_prompt", ""),
        "rationale": visual_output.get("rationale", ""),
        "brand_rules_applied": visual_output.get("brand_rules_applied", []),
        "status": "draft",
    }

    scene_slug = _slugify(scene)[:40]
    output_path = _build_output_path(
        OUTPUTS_DIR / "image-prompts", target_date, persona, scene_slug
    )
    _write_json(package, output_path)
    return output_path


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "_", text)
    return text


def _build_output_path(
    directory: Path,
    target_date: str,
    persona: str,
    scene_slug: str,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{target_date}_{persona}_{scene_slug}.json"
    return directory / filename


def _write_json(data: dict, path: Path) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
