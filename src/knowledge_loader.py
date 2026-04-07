"""
knowledge_loader.py — File injection de documentos markdown de knowledge/

Fase 1: carga y concatena docs de knowledge/ directamente en el system prompt.
No usa embeddings ni vector store para estos documentos.
"""

from pathlib import Path
from typing import Optional
from src.config import KNOWLEDGE_DIR, AGENTS_DIR


def load_document(path: Path) -> str:
    """Lee un archivo markdown y retorna su contenido."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def load_knowledge_section(section: str) -> str:
    """
    Carga todos los docs de una sección específica de knowledge/.
    section: 'brand', 'operations', 'finance', 'content'
    """
    section_dir = KNOWLEDGE_DIR / section
    if not section_dir.exists():
        return ""

    docs = []
    for md_file in sorted(section_dir.glob("*.md")):
        content = load_document(md_file)
        if content:
            docs.append(f"## [{md_file.stem}]\n\n{content}")

    return "\n\n---\n\n".join(docs)


def load_all_knowledge(sections: Optional[list[str]] = None) -> str:
    """
    Carga y concatena todos los documentos de knowledge/.
    sections: lista de secciones a cargar. Si None, carga todas.
    """
    all_sections = ["brand", "operations", "finance", "content"]
    target_sections = sections if sections else all_sections

    parts = []
    for section in target_sections:
        content = load_knowledge_section(section)
        if content:
            parts.append(f"# KNOWLEDGE: {section.upper()}\n\n{content}")

    return "\n\n===\n\n".join(parts)


def load_agent_prompt(agent_name: str) -> str:
    """
    Carga el system prompt de un agente desde agents/{agent_name}/system-prompt.md
    """
    prompt_path = AGENTS_DIR / agent_name / "system-prompt.md"
    return load_document(prompt_path)


def load_persona_voice(persona: str) -> str:
    """
    Carga la definición de voz/personalidad de un persona desde agents/personas/{persona}.md
    """
    persona_path = AGENTS_DIR / "personas" / f"{persona}.md"
    return load_document(persona_path)
