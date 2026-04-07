"""
persona_engine.py — Motor de voz y visual para Dante y Valeria

Dos modos de operación:
  - voice:  genera captions/copies en la voz del personaje
            inyecta agents/personas/{persona}.md + knowledge/brand/avatars.md
            OUTPUT: dict con caption, hashtags, rationale, brand_rules_applied

  - visual: ensambla master prompt para Midjourney/SDXL
            RAG sobre UGC/{persona}/{face,body}.md según el framing solicitado
            INPUT: descripción de escena + ángulo + contexto
            OUTPUT: dict con master_prompt, negative_prompt, rationale

No es subclase de BaseAgent — es un servicio stateless sin historial de sesión.
Cada llamada es independiente.
"""

import json
import re
from typing import Literal

import anthropic

from src.config import ANTHROPIC_API_KEY, SUBAGENT_MODEL
from src.knowledge_loader import load_persona_voice, load_knowledge_section
from src.vector_store import query_ugc

Persona = Literal["dante", "valeria", "institutional"]
Framing = Literal["portrait", "full_body", "close_up"]


class PersonaEngine:
    """
    Motor de generación de contenido para los personajes de Sativa Liquor.

    Uso — modo voice:
        engine = PersonaEngine()
        result = engine.generate_voice("dante", brief_dict)
        # result["content"]["caption"]  → el texto listo para publicar

    Uso — modo visual:
        result = engine.generate_visual("valeria", scene="neón y lluvia", angle="3/4", framing="portrait")
        # result["content"]["master_prompt"]  → el prompt para Midjourney/SDXL
    """

    # Negative prompt fijo de marca — nunca configurable
    NEGATIVE_PROMPT = (
        "kawaii, cute, pastel colors, childish, manga, anime, illustration, cartoon, "
        "marijuana leaf, cannabis leaf, weed leaf, generic stock photo, corporate, "
        "white background, studio lighting, food photography style, heladería, "
        "candy, sprinkles, umbrella straw, colorful straws arrangement"
    )

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = SUBAGENT_MODEL

    # ─── MODO VOICE ────────────────────────────────────────────────────────────

    def generate_voice(self, persona: Persona, brief: dict) -> dict:
        """
        Genera caption en la voz del personaje a partir de un brief del CMO.

        Args:
            persona: "dante" | "valeria" | "institutional"
            brief:   dict con las claves del CMO output (topic, emotional_objective, etc.)

        Returns:
            dict con estructura:
            {
              "content": {
                "caption": str,
                "hashtags": list[str],
                "content_type": str,
                "visual_note": str
              },
              "rationale": str,
              "brand_rules_applied": list[str]
            }
        """
        system = self._build_voice_system_prompt(persona)
        user_message = self._format_brief_as_prompt(brief)

        raw = self._call_claude(system, user_message)
        return self._parse_json_response(raw)

    def _build_voice_system_prompt(self, persona: Persona) -> str:
        """Construye el system prompt para modo voice."""
        if persona == "institutional":
            brand_knowledge = load_knowledge_section("brand")
            return f"""Eres la voz institucional de Sativa Liquor para el contenido del jueves.
No eres Dante ni Valeria. Eres la marca hablando directamente: directa, cinematográfica, nunca genérica.

Tu trabajo es generar el anuncio semanal de agenda (line-up, promos, horarios, domicilios).
Tono: impactante, conciso, sin flyers aburridos. El texto siempre va sobre imágenes cinematográficas.

<brand_context>
{brand_knowledge}
</brand_context>

Responde SIEMPRE en JSON con esta estructura exacta, sin texto fuera del JSON:
{{
  "content": {{
    "caption": "el texto del post",
    "hashtags": ["#tag1", "#tag2"],
    "content_type": "reel | carousel | story | static",
    "visual_note": "indicación para el editor (1 línea)"
  }},
  "rationale": "por qué esta es la decisión correcta",
  "brand_rules_applied": ["reglas aplicadas"]
}}"""

        persona_voice = load_persona_voice(persona)
        avatars_knowledge = load_knowledge_section("brand")

        return f"""{persona_voice}

<brand_context>
{avatars_knowledge}
</brand_context>"""

    def _format_brief_as_prompt(self, brief: dict) -> str:
        """Convierte el dict del CMO en un mensaje de usuario legible."""
        content = brief.get("content", brief)  # soporta brief directo o wrapped
        lines = [
            "Genera el contenido para este brief:",
            "",
            f"Tema: {content.get('topic', 'no especificado')}",
            f"Tipo de contenido: {content.get('content_type', 'reel')}",
            f"Fase del protocolo: {content.get('day_phase', 'no especificado')}",
            f"Escena/contexto visual: {content.get('scene_brief', 'no especificado')}",
            f"Objetivo emocional: {content.get('emotional_objective', 'no especificado')}",
            f"Objetivo de negocio: {content.get('business_objective', 'no especificado')}",
        ]

        constraints = content.get("constraints", [])
        if constraints:
            lines.append(f"Restricciones adicionales: {', '.join(constraints)}")

        ref_data = content.get("reference_data", "")
        if ref_data and ref_data != "Sin datos previos":
            lines.append(f"Datos de referencia: {ref_data}")

        return "\n".join(lines)

    # ─── MODO VISUAL ───────────────────────────────────────────────────────────

    def generate_visual(
        self,
        persona: Persona,
        scene: str,
        angle: str = "3/4",
        framing: Framing = "portrait",
        n_ugc_results: int = 4,
    ) -> dict:
        """
        Genera master prompt para Midjourney/SDXL usando RAG sobre UGC/.

        Args:
            persona:  "dante" | "valeria"
            scene:    descripción de la escena ("callejón urbano, atardecer dorado")
            angle:    ángulo de cámara ("3/4 izquierdo", "frontal", "contrapicado")
            framing:  "portrait" | "full_body" | "close_up"
            n_ugc_results: chunks de UGC a recuperar por RAG

        Returns:
            dict con estructura:
            {
              "content": {
                "master_prompt": str,
                "negative_prompt": str,
                "scene": str,
                "angle": str,
                "framing": str
              },
              "rationale": str,
              "brand_rules_applied": list[str]
            }
        """
        file_type = self._framing_to_file_type(framing)
        ugc_context = query_ugc(
            query=f"{scene} {angle} {framing}",
            persona=persona,
            file_type=file_type,
            n_results=n_ugc_results,
        )

        visual_codes = load_knowledge_section("brand")
        system = self._build_visual_system_prompt(persona, framing, ugc_context, visual_codes)
        user_message = (
            f"Genera el master prompt de imagen con estos parámetros:\n"
            f"Escena: {scene}\n"
            f"Ángulo: {angle}\n"
            f"Encuadre: {framing}"
        )

        raw = self._call_claude(system, user_message)
        result = self._parse_json_response(raw)

        # Garantizar negative_prompt de marca siempre presente
        if "content" in result:
            result["content"]["negative_prompt"] = self.NEGATIVE_PROMPT
            result["content"]["scene"] = scene
            result["content"]["angle"] = angle
            result["content"]["framing"] = framing

        return result

    def _build_visual_system_prompt(
        self,
        persona: Persona,
        framing: Framing,
        ugc_context: str,
        visual_codes: str,
    ) -> str:
        """Construye el system prompt para modo visual con contexto RAG."""
        return f"""Eres un especialista en prompts para generación de imágenes con IA (Midjourney/SDXL).
Tu tarea es ensamblar un master prompt técnico y preciso para generar una imagen del personaje
{persona.capitalize()} de Sativa Liquor, en el encuadre "{framing}".

<ugc_biometric_context>
A continuación está la información biométrica y técnica del personaje recuperada de la base de datos.
Úsala como fuente de verdad para describir al personaje. No contradigas ningún detalle físico.

{ugc_context if ugc_context else "No se encontró contexto biométrico específico."}
</ugc_biometric_context>

<brand_visual_codes>
{visual_codes}
</brand_visual_codes>

<prompt_rules>
- El master prompt debe estar en inglés (estándar para Midjourney/SDXL)
- Incluir: descripción del personaje (rasgos físicos clave), escena/ambiente, iluminación,
  ángulo de cámara, estilo fotográfico, mood
- Estilo fotográfico de Sativa: oscuro, urbano, contraste alto, neón, fotografía callejera
- NUNCA incluir: kawaii, cute, pastel, anime, cartoon, marijuana leaf, cannabis
- El prompt debe tener entre 50-120 palabras — denso y técnico, no poético
- Incluir parámetros de Midjourney al final si aplica (--ar 9:16 para Reels, --ar 1:1 para feed)
</prompt_rules>

Responde SIEMPRE en JSON con esta estructura exacta, sin texto fuera del JSON:
{{
  "content": {{
    "master_prompt": "el prompt completo en inglés listo para copiar en Midjourney/SDXL"
  }},
  "rationale": "qué secciones del UGC se usaron y por qué",
  "brand_rules_applied": ["reglas visuales de marca que se aplicaron"]
}}"""

    def _framing_to_file_type(self, framing: Framing) -> str:
        """Mapea el framing al tipo de archivo UGC a consultar."""
        if framing in ("full_body",):
            return "body"
        return "face"  # portrait y close_up usan face.md

    # ─── UTILIDADES ────────────────────────────────────────────────────────────

    def _call_claude(self, system: str, user_message: str) -> str:
        """Llamada no-streaming a Claude. Retorna el texto raw de la respuesta."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    def _parse_json_response(self, raw: str) -> dict:
        """
        Extrae y parsea JSON del response.
        Tolerante a markdown code fences (```json ... ```) que Claude a veces añade.
        """
        text = raw.strip()

        # Eliminar code fences si existen
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence_match:
            text = fence_match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Retornar el texto raw en un envelope de error para no romper el flujo
            return {
                "content": {"raw_response": raw},
                "rationale": "Error: la respuesta no era JSON válido",
                "brand_rules_applied": [],
                "_parse_error": True,
            }
