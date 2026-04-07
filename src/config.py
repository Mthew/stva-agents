from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", BASE_DIR / "knowledge"))
UGC_DIR = Path(os.getenv("UGC_DIR", BASE_DIR / "UGC"))
AGENTS_DIR = BASE_DIR / "agents"
MEMORY_DIR = Path(os.getenv("MEMORY_DIR", BASE_DIR / "memory"))
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
OUTPUTS_DIR = Path(os.getenv("OUTPUTS_DIR", BASE_DIR / "outputs"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY", "")

# Claude models por jerarquía de agente
CEO_MODEL = "claude-opus-4-6"
SUBAGENT_MODEL = "claude-sonnet-4-6"

# ChromaDB — directorio local donde se persiste el índice
CHROMA_DIR = BASE_DIR / ".chroma"

# Sesión por defecto
DEFAULT_SESSION_ID = "default"
