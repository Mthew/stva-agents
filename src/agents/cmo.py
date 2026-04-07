"""
cmo.py — CMO Agent de Sativa Liquor

Estratega de contenido. Genera briefs estructurados para el Persona Engine.
No escribe captions — decide qué se dice, quién lo dice y por qué.

Invocado programáticamente por el WorkflowRunner (no interactivo).
Usa _get_response() no-streaming para retornar JSON parseado.
"""

import json
import re
from datetime import date as date_type

from src.config import SUBAGENT_MODEL
from src.agents.base_agent import BaseAgent
from src.knowledge_loader import load_agent_prompt, load_knowledge_section


class CMOAgent(BaseAgent):
    """
    El CMO de Sativa Liquor.

    Knowledge inyectado en el system prompt:
    - agents/cmo/system-prompt.md
    - knowledge/brand/ (brand.md, avatars.md, visual-codes.md)
    - knowledge/content/ (content-calendar.md, published-content.md)
    """

    model = SUBAGENT_MODEL
    agent_name = "cmo"

    def build_system_prompt(self) -> str:
        agent_prompt = load_agent_prompt("cmo")
        brand_knowledge = load_knowledge_section("brand")
        content_knowledge = load_knowledge_section("content")

        return (
            f"{agent_prompt}\n\n"
            f"<brand_knowledge>\n{brand_knowledge}\n</brand_knowledge>\n\n"
            f"<content_knowledge>\n{content_knowledge}\n</content_knowledge>"
        )

    def generate_brief(
        self,
        target_date: str,
        day_name: str,
        override: str = "",
    ) -> dict:
        """
        Genera un brief estructurado para el día.

        Args:
            target_date: fecha en formato "YYYY-MM-DD"
            day_name:    nombre del día en español ("lunes", "martes", ..., "domingo")
            override:    instrucción adicional del CEO (opcional)

        Returns:
            dict con el JSON del CMO:
            {
              "content": {
                "persona": "dante | valeria | institutional",
                "content_type": "reel | carousel | story | static",
                "day_phase": "lun-mie | jueves | vie-dom",
                "topic": str,
                "scene_brief": str,
                "emotional_objective": str,
                "business_objective": str,
                "constraints": list[str],
                "reference_data": str
              },
              "rationale": str,
              "brand_rules_applied": list[str]
            }
        """
        user_message = (
            f"Genera el brief de contenido para:\n"
            f"Fecha: {target_date}\n"
            f"Día: {day_name}"
        )
        if override:
            user_message += f"\nInstrucción del CEO: {override}"

        messages = [{"role": "user", "content": user_message}]
        raw = self._get_response(messages)
        return self._parse_json_response(raw)

    def generate_creative_brief(
        self,
        voice_output: dict,
        visual_output: dict,
        cmo_brief: dict,
        target_date: str,
    ) -> dict:
        """
        Síntesis final: combina voice output + visual output + brief original
        en un paquete completo listo para revisión humana.

        Returns:
            dict con estructura:
            {
              "content": {
                "date": str,
                "persona": str,
                "content_type": str,
                "caption_draft": str,
                "hashtags": list[str],
                "visual_master_prompt": str,
                "negative_prompt": str,
                "production_notes": str
              },
              "rationale": str,
              "brand_rules_applied": list[str],
              "status": "pending_review"
            }
        """
        # Extraer los campos relevantes de cada output
        voice_content = voice_output.get("content", {})
        visual_content = visual_output.get("content", {})
        brief_content = cmo_brief.get("content", cmo_brief)

        persona = brief_content.get("persona", "dante")
        content_type = brief_content.get("content_type", "reel")

        user_message = (
            f"Sintetiza el brief creativo final para:\n"
            f"Fecha: {target_date}\n"
            f"Personaje: {persona}\n"
            f"Formato: {content_type}\n\n"
            f"CAPTION DRAFT:\n{voice_content.get('caption', '')}\n\n"
            f"HASHTAGS: {', '.join(voice_content.get('hashtags', []))}\n\n"
            f"MASTER PROMPT VISUAL:\n{visual_content.get('master_prompt', '')}\n\n"
            f"NOTA VISUAL DEL PERSONAJE: {voice_content.get('visual_note', '')}\n\n"
            f"BRIEF ORIGINAL DEL CMO:\n{json.dumps(brief_content, ensure_ascii=False, indent=2)}\n\n"
            "Genera el brief creativo final integrado en JSON con estas claves exactas:\n"
            '{"content": {"date", "persona", "content_type", "caption_draft", "hashtags", '
            '"visual_master_prompt", "negative_prompt", "production_notes"}, '
            '"rationale", "brand_rules_applied", "status": "pending_review"}'
        )

        messages = [{"role": "user", "content": user_message}]
        raw = self._get_response(messages)
        result = self._parse_json_response(raw)

        # Garantizar status siempre presente
        result["status"] = "pending_review"
        return result

    def _parse_json_response(self, raw: str) -> dict:
        """
        Extrae y parsea JSON. Tolerante a code fences de markdown.
        """
        text = raw.strip()

        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence_match:
            text = fence_match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "content": {"raw_response": raw},
                "rationale": "Error: la respuesta no era JSON válido",
                "brand_rules_applied": [],
                "_parse_error": True,
            }
