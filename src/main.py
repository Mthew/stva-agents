"""
main.py — CLI de Sativa Agents

Punto de entrada único para interactuar con el sistema de agentes.

Uso:
    python -m src.main chat                     # Conversar con el CEO
    python -m src.main chat --session mi-sesion # Sesión nombrada
    python -m src.main memory list              # Ver sesiones guardadas
    python -m src.main memory clear             # Borrar sesión actual
    python -m src.main index                    # Re-indexar UGC/ en ChromaDB
"""

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich import print as rprint

from src.config import DEFAULT_SESSION_ID, BASE_DIR

app = typer.Typer(help="Sativa Agents — Sistema multi-agente para Sativa Liquor")
memory_app = typer.Typer(help="Gestión de historial de sesiones")
generate_app = typer.Typer(help="Generación de assets de contenido")
app.add_typer(memory_app, name="memory")
app.add_typer(generate_app, name="generate")

console = Console()


def _print_header():
    console.print(Panel(
        Text("SATIVA BOSS — CEO Agent", justify="center", style="bold green"),
        subtitle="[dim]Escribe 'exit' o presiona Ctrl+C para salir[/dim]",
        border_style="green",
    ))


def _print_user(msg: str):
    console.print(f"\n[bold cyan]Mateo:[/bold cyan] {msg}")


def _print_agent_prefix():
    console.print("\n[bold green]Sativa Boss:[/bold green] ", end="")


@app.command()
def chat(
    session: str = typer.Option(DEFAULT_SESSION_ID, "--session", "-s", help="ID de sesión"),
    no_history: bool = typer.Option(False, "--no-history", help="Iniciar sin cargar historial previo"),
):
    """Conversación interactiva con el CEO Agent (Sativa Boss)."""
    from src.agents.ceo import CEOAgent
    from src.memory.session_store import load_session, list_sessions

    agent = CEOAgent(session_id=session)

    if no_history:
        agent.reset_session()

    _print_header()

    # Mostrar contexto de sesión si hay historial
    history = load_session(session)
    if history:
        msg_count = len(history)
        console.print(f"[dim]Sesión '{session}' cargada — {msg_count} mensajes previos[/dim]\n")
    else:
        console.print(f"[dim]Nueva sesión: '{session}'[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]Mateo[/bold cyan]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Hasta la próxima, parce.[/dim]")
            break

        if user_input.lower() in ("exit", "quit", "salir"):
            console.print("[dim]Hasta la próxima, parce.[/dim]")
            break

        if not user_input.strip():
            continue

        _print_agent_prefix()
        try:
            agent.chat(user_input, stream=True)
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")


@memory_app.command("list")
def memory_list():
    """Lista todas las sesiones guardadas."""
    from src.memory.session_store import list_sessions

    sessions = list_sessions()
    if not sessions:
        console.print("[dim]No hay sesiones guardadas.[/dim]")
        return

    console.print(Panel("Sesiones guardadas", border_style="green"))
    for s in sessions:
        console.print(
            f"  [bold]{s['session_id']}[/bold] — "
            f"{s['message_count']} mensajes — "
            f"[dim]{s['updated_at'][:19]}[/dim]"
        )


@memory_app.command("clear")
def memory_clear(
    session: str = typer.Option(DEFAULT_SESSION_ID, "--session", "-s", help="ID de sesión a borrar"),
):
    """Borra el historial de una sesión."""
    from src.memory.session_store import clear_session

    clear_session(session)
    console.print(f"[green]Sesión '{session}' borrada.[/green]")


@app.command()
def run(
    workflow: str = typer.Argument(..., help="Nombre del workflow (ej: weekly-content)"),
    date_override: Optional[str] = typer.Option(None, "--date", "-d", help="Fecha YYYY-MM-DD"),
):
    """Ejecuta un workflow de contenido definido en workflows/."""
    from src.workflows.runner import WorkflowRunner

    workflow_path = BASE_DIR / "workflows" / f"{workflow}.yaml"
    if not workflow_path.exists():
        console.print(f"[red]Workflow '{workflow}' no encontrado en workflows/[/red]")
        raise typer.Exit(1)

    overrides = {}
    if date_override:
        overrides["current_date"] = date_override

    console.print(Panel(
        Text(f"Ejecutando workflow: {workflow}", justify="center", style="bold green"),
        border_style="green",
    ))

    runner = WorkflowRunner(workflow_path)

    steps = runner.config.get("steps", [])
    results = {}
    try:
        # Inicializar contexto del runner para poder mostrar progreso
        from datetime import date
        today = date.today()
        from src.workflows.runner import WorkflowRunner as WR
        runner._runtime_context = {
            "current_date": date_override or today.isoformat(),
            "current_day_name": WR._day_name_es(today),
            **overrides,
        }
        if date_override:
            try:
                od = date.fromisoformat(date_override)
                runner._runtime_context["current_day_name"] = WR._day_name_es(od)
            except ValueError:
                pass

        for step in steps:
            desc = step.get("description", step["id"])
            with console.status(f"[bold green]{desc}...[/bold green]"):
                runner._execute_step(step)
            console.print(f"  [green]✓[/green] {step['id']}")

        results = runner._step_outputs

    except Exception as e:
        console.print(f"\n[red]Error en el workflow: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[green]Workflow completado.[/green]")
    target_date = runner._runtime_context.get("current_date", "")
    console.print(f"[dim]Outputs guardados en outputs/ — fecha: {target_date}[/dim]")


@generate_app.command("image")
def generate_image(
    persona: str = typer.Option(..., "--persona", "-p", help="dante | valeria"),
    scene: str = typer.Option(..., "--scene", "-s", help="Descripción de la escena"),
    angle: str = typer.Option("3/4", "--angle", "-a", help="Ángulo de cámara"),
    framing: str = typer.Option("portrait", "--framing", "-f", help="portrait | full_body | close_up"),
    save: bool = typer.Option(True, "--save/--no-save", help="Guardar en outputs/image-prompts/"),
):
    """Genera un master prompt de imagen para Midjourney/SDXL."""
    from src.personas.persona_engine import PersonaEngine
    from src.tools.image_prompt_generator import save_image_prompt
    from datetime import date

    if persona not in ("dante", "valeria"):
        console.print("[red]Persona debe ser 'dante' o 'valeria'[/red]")
        raise typer.Exit(1)

    engine = PersonaEngine()
    with console.status(f"[bold green]Generando prompt visual para {persona.capitalize()}...[/bold green]"):
        result = engine.generate_visual(persona=persona, scene=scene, angle=angle, framing=framing)

    if result.get("_parse_error"):
        console.print("[red]Error al generar el prompt.[/red]")
        console.print(result.get("content", {}).get("raw_response", ""))
        raise typer.Exit(1)

    master_prompt = result.get("content", {}).get("master_prompt", "")
    console.print(Panel(master_prompt, title=f"Master Prompt — {persona.capitalize()}", border_style="green"))
    console.print(f"\n[dim]Negative prompt:[/dim] {result.get('content', {}).get('negative_prompt', '')[:80]}...")

    if save:
        path = save_image_prompt(result, persona, scene, date.today().isoformat())
        console.print(f"\n[dim]Guardado en: {path}[/dim]")


@app.command()
def index(
    force: bool = typer.Option(False, "--force", "-f", help="Forzar re-indexado aunque ya exista"),
):
    """Indexa los archivos UGC/ en ChromaDB para búsqueda semántica."""
    from src.vector_store import get_ugc_store

    with console.status("[bold green]Indexando archivos UGC/...[/bold green]"):
        store = get_ugc_store()
        if force:
            store.index_ugc_files(force_reindex=True)
        else:
            store.index_ugc_files()

    count = store.collection.count()
    console.print(f"[green]Indexado completo — {count} chunks en ChromaDB.[/green]")


if __name__ == "__main__":
    app()
