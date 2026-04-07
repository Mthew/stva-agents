"""
base_agent.py — Clase base para todos los agentes de Sativa

Maneja:
- Llamadas a la Claude API con historial
- Inyección de knowledge y system prompt
- Persistencia de sesión
"""

from typing import Optional

import anthropic

from src.config import ANTHROPIC_API_KEY, SUBAGENT_MODEL
from src.memory.session_store import load_session, append_message


class BaseAgent:
    """
    Clase base para todos los agentes de Sativa Liquor.
    Las subclases definen su system prompt, modelo y knowledge.
    """

    model: str = SUBAGENT_MODEL
    agent_name: str = "base"

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self._system_prompt: Optional[str] = None

    def build_system_prompt(self) -> str:
        """
        Construye el system prompt completo del agente.
        Las subclases sobreescriben este método para inyectar knowledge.
        """
        raise NotImplementedError

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            self._system_prompt = self.build_system_prompt()
        return self._system_prompt

    def get_history(self) -> list[dict]:
        """Carga el historial de mensajes de la sesión actual."""
        return load_session(self.session_id)

    def chat(self, user_message: str, stream: bool = True) -> str:
        """
        Envía un mensaje y retorna la respuesta del agente.
        Persiste ambos mensajes en la sesión.
        """
        messages = self.get_history()
        messages.append({"role": "user", "content": user_message})

        if stream:
            response_text = self._stream_response(messages)
        else:
            response_text = self._get_response(messages)

        # Persistir user message y respuesta
        append_message("user", user_message, self.session_id)
        append_message("assistant", response_text, self.session_id)

        return response_text

    def _get_response(self, messages: list[dict]) -> str:
        """Llamada no-streaming a la API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            messages=messages,
        )
        return response.content[0].text

    def _stream_response(self, messages: list[dict]) -> str:
        """Llamada streaming a la API. Imprime en tiempo real y retorna el texto completo."""
        full_text = ""
        with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=self.system_prompt,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
                full_text += text
        print()  # newline al terminar
        return full_text

    def reset_session(self) -> None:
        """Borra el historial de la sesión actual."""
        from src.memory.session_store import clear_session
        clear_session(self.session_id)
        self._system_prompt = None  # Fuerza rebuild en próxima llamada
