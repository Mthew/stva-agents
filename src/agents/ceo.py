"""
ceo.py — CEO Agent (Sativa Boss)

El orquestador central. Usa claude-opus-4-6 y tiene acceso a todo el knowledge base.
Es el único punto de entrada para el usuario — delega a subagentes según la tarea.
"""

from src.config import CEO_MODEL
from src.agents.base_agent import BaseAgent
from src.knowledge_loader import load_agent_prompt, load_all_knowledge


class CEOAgent(BaseAgent):
    """
    El Sativa Boss. Orquestador central de todos los agentes.

    Knowledge inyectado:
    - System prompt de agents/ceo/system-prompt.md
    - Todo el contenido de knowledge/ (brand, operations, finance, content)
    """

    model = CEO_MODEL
    agent_name = "ceo"

    def build_system_prompt(self) -> str:
        agent_prompt = load_agent_prompt("ceo")
        knowledge = load_all_knowledge()

        return f"""{agent_prompt}

<knowledge_base>
A continuación está tu base de conocimiento completa. Úsala como fuente de verdad
para todas tus respuestas. No contradigas ninguna regla o principio definido aquí.

{knowledge}
</knowledge_base>

<session_context>
Estás en una conversación continua con Mateo, el fundador y co-operador de Sativa Liquor.
Él es Ingeniero de Software y maneja el lado técnico y estratégico del negocio.
Su hermana maneja las operaciones en el local.
El negocio está en fase de bootstrapping — el local en Altavista está en construcción
y el cashflow es la prioridad táctica número uno.
</session_context>"""
