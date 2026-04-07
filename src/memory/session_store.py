"""
session_store.py — Persistencia de historial de conversaciones en JSON

Guarda el historial de mensajes entre sesiones en memory/{session_id}.json
para que el CEO Agent recuerde el contexto entre ejecuciones del CLI.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.config import MEMORY_DIR, DEFAULT_SESSION_ID


def _session_path(session_id: str) -> Path:
    MEMORY_DIR.mkdir(exist_ok=True)
    return MEMORY_DIR / f"{session_id}.json"


def load_session(session_id: str = DEFAULT_SESSION_ID) -> list[dict]:
    """
    Carga el historial de mensajes de una sesión.
    Retorna lista de mensajes en formato Anthropic: [{role, content}, ...]
    """
    path = _session_path(session_id)
    if not path.exists():
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("messages", [])
    except (json.JSONDecodeError, KeyError):
        return []


def save_session(
    messages: list[dict],
    session_id: str = DEFAULT_SESSION_ID,
    max_messages: int = 100,
) -> None:
    """
    Persiste el historial de mensajes en disco.
    Mantiene solo los últimos max_messages para evitar que el contexto crezca indefinidamente.
    """
    # Preservar siempre al menos el primer mensaje del sistema si existe
    trimmed = messages[-max_messages:] if len(messages) > max_messages else messages

    data = {
        "session_id": session_id,
        "updated_at": datetime.now().isoformat(),
        "message_count": len(trimmed),
        "messages": trimmed,
    }

    path = _session_path(session_id)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_session(session_id: str = DEFAULT_SESSION_ID) -> None:
    """Borra el historial de una sesión."""
    path = _session_path(session_id)
    if path.exists():
        path.unlink()


def list_sessions() -> list[dict]:
    """Lista todas las sesiones disponibles con metadata."""
    MEMORY_DIR.mkdir(exist_ok=True)
    sessions = []
    for json_file in sorted(MEMORY_DIR.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            sessions.append({
                "session_id": data.get("session_id", json_file.stem),
                "updated_at": data.get("updated_at", ""),
                "message_count": data.get("message_count", 0),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return sessions


def append_message(
    role: str,
    content: str,
    session_id: str = DEFAULT_SESSION_ID,
) -> list[dict]:
    """
    Añade un mensaje al historial y persiste inmediatamente.
    Retorna el historial actualizado.
    """
    messages = load_session(session_id)
    messages.append({"role": role, "content": content})
    save_session(messages, session_id)
    return messages
