"""
runner.py — Ejecutor de workflows YAML

Lee un archivo YAML de workflows/ y ejecuta los steps en orden,
pasando outputs entre pasos mediante resolución de placeholders.

Uso:
    runner = WorkflowRunner(Path("workflows/weekly-content.yaml"))
    results = runner.run()
    results = runner.run(overrides={"current_date": "2026-04-10"})
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

from src.config import BASE_DIR


class WorkflowRunner:
    """
    Ejecuta workflows definidos en YAML.

    Resuelve dependencias entre pasos, pasa outputs entre steps
    via placeholders {step_id.key.subkey}, y persiste resultados
    en los directorios de outputs/ especificados.
    """

    def __init__(self, workflow_path: Path):
        with open(workflow_path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        self._step_outputs: dict[str, dict] = {}
        self._agents: dict[str, Any] = {}

    def run(self, overrides: dict | None = None) -> dict:
        """
        Ejecuta todos los steps del workflow en orden.

        Args:
            overrides: dict con valores para sobreescribir placeholders del YAML.
                       Ej: {"current_date": "2026-04-10"}

        Returns:
            dict con todos los outputs por step_id
        """
        # Contexto base del runtime
        today = date.today()
        self._runtime_context = {
            "current_date": today.isoformat(),
            "current_day_name": self._day_name_es(today),
            **(overrides or {}),
        }

        # Si se pasó una fecha override, recalcular el día
        if overrides and "current_date" in overrides:
            try:
                override_date = date.fromisoformat(overrides["current_date"])
                self._runtime_context["current_day_name"] = self._day_name_es(override_date)
            except ValueError:
                pass

        steps = self.config.get("steps", [])
        for step in steps:
            self._execute_step(step)

        return self._step_outputs

    def _execute_step(self, step: dict) -> None:
        """Ejecuta un step individual y guarda su output en _step_outputs."""
        step_id = step["id"]
        agent_name = step["agent"]
        action = step["action"]
        raw_inputs = step.get("inputs", {})
        output_keys = step.get("outputs", [])
        save_to = step.get("save_to")

        # Resolver inputs (reemplaza placeholders con valores reales)
        resolved_inputs = {k: self._resolve(v) for k, v in raw_inputs.items()}

        # Obtener o inicializar el agente/engine
        agent = self._get_agent(agent_name)

        # Ejecutar la acción
        result = self._call_action(agent, action, resolved_inputs)

        # Guardar output con los nombres declarados en el YAML
        for key in output_keys:
            self._step_outputs[key] = result

        # También guardar bajo el step_id para resolución de placeholders
        self._step_outputs[step_id] = result

        # Persistir en disco si se especificó save_to
        if save_to:
            self._save_step_output(result, save_to, step_id, resolved_inputs)

    def _call_action(self, agent: Any, action: str, inputs: dict) -> dict:
        """Llama al método `action` del agente con los inputs resueltos."""
        method = getattr(agent, action)

        # Mapear los inputs del YAML a los parámetros del método
        if action == "generate_brief":
            return method(
                target_date=inputs.get("date", ""),
                day_name=inputs.get("day_name", ""),
                override=inputs.get("override", ""),
            )
        elif action == "generate_voice":
            return method(
                persona=inputs.get("persona", "dante"),
                brief=inputs.get("brief", {}),
            )
        elif action == "generate_visual":
            return method(
                persona=inputs.get("persona", "dante"),
                scene=inputs.get("scene", ""),
                angle=inputs.get("angle", "3/4"),
                framing=inputs.get("framing", "portrait"),
            )
        elif action == "generate_creative_brief":
            return method(
                voice_output=inputs.get("voice_output", {}),
                visual_output=inputs.get("visual_output", {}),
                cmo_brief=inputs.get("cmo_brief", {}),
                target_date=inputs.get("date", ""),
            )
        else:
            # Fallback genérico: pasar inputs como kwargs
            return method(**inputs)

    def _resolve(self, value: Any) -> Any:
        """
        Resuelve un valor del YAML reemplazando placeholders {key} o {step.key.subkey}.

        Ejemplos:
          "{current_date}"                  → "2026-04-07"
          "{cmo_brief.content.persona}"     → "dante"
          "{cmo_brief}"                     → el dict completo del step cmo_brief
        """
        if not isinstance(value, str):
            return value

        # Placeholder simple sin puntos — puede ser contexto runtime o un output completo
        if re.fullmatch(r"\{(\w+)\}", value):
            key = value[1:-1]
            if key in self._runtime_context:
                return self._runtime_context[key]
            if key in self._step_outputs:
                return self._step_outputs[key]
            return value

        # Placeholder con dot notation — acceso a campo anidado
        dot_match = re.fullmatch(r"\{([\w.]+)\}", value)
        if dot_match:
            path = dot_match.group(1).split(".")
            root_key = path[0]
            obj = self._step_outputs.get(root_key) or self._runtime_context.get(root_key)
            if obj is None:
                return value
            return self._dot_access(obj, path[1:])

        return value

    def _dot_access(self, obj: Any, keys: list[str]) -> Any:
        """Navega un dict/list anidado via lista de claves."""
        for key in keys:
            if isinstance(obj, dict):
                obj = obj.get(key, "")
            else:
                return ""
        return obj

    def _get_agent(self, agent_name: str) -> Any:
        """Lazy-inicializa y cachea los agentes/engines por nombre."""
        if agent_name not in self._agents:
            if agent_name == "cmo":
                from src.agents.cmo import CMOAgent
                self._agents[agent_name] = CMOAgent()
            elif agent_name == "persona_engine":
                from src.personas.persona_engine import PersonaEngine
                self._agents[agent_name] = PersonaEngine()
            elif agent_name == "ceo":
                from src.agents.ceo import CEOAgent
                self._agents[agent_name] = CEOAgent()
            else:
                raise ValueError(f"Agente desconocido: '{agent_name}'")
        return self._agents[agent_name]

    def _save_step_output(
        self,
        result: dict,
        save_to: str,
        step_id: str,
        inputs: dict,
    ) -> None:
        """Persiste el output de un step en el directorio especificado."""
        from src.tools.content_generator import save_content_output
        from src.tools.image_prompt_generator import save_image_prompt

        target_date = self._runtime_context.get("current_date", date.today().isoformat())
        output_dir = save_to

        if output_dir == "outputs/content":
            cmo_brief = inputs.get("brief", self._step_outputs.get("cmo_brief", {}))
            save_content_output(cmo_brief, result, target_date)

        elif output_dir == "outputs/image-prompts":
            persona = inputs.get("persona", "dante")
            scene = inputs.get("scene", "sin escena")
            save_image_prompt(result, persona, scene, target_date)

        elif output_dir == "outputs/briefs":
            self._save_brief(result, target_date)

    def _save_brief(self, brief: dict, target_date: str) -> None:
        """Guarda el creative brief en outputs/briefs/."""
        from src.config import OUTPUTS_DIR

        briefs_dir = OUTPUTS_DIR / "briefs"
        briefs_dir.mkdir(parents=True, exist_ok=True)

        content = brief.get("content", {})
        persona = content.get("persona", "unknown")
        content_type = content.get("content_type", "post")

        filename = f"{target_date}_{persona}_{content_type}_brief.json"
        path = briefs_dir / filename
        path.write_text(
            json.dumps(brief, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _day_name_es(d: date) -> str:
        """Retorna el nombre del día en español."""
        names = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        return names[d.weekday()]


# ─── import re necesario para _resolve ───────────────────────────────────────
import re
