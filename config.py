# Configurações e constantes do sistema

import json
import os
from pathlib import Path

# Porta de execução do servidor Flask
PORT: int = int(os.getenv("PORT", "8001"))

# Chaves e credenciais de integração externa
GEMINI_KEY: str = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
GOOGLE_CLIENT_ID: str = os.getenv(
    "GOOGLE_CLIENT_ID",
    "418686361464-m2hip9tp1v15sr3lj14iip3q956c756g.apps.googleusercontent.com",
)

# Tempo limite (segundos) da chamada ao Gemini. O enunciado cita 6.0s, mas o guia detalhado leva de 13 a 26s; ajustável por variável de ambiente.
GEMINI_TIMEOUT: float = float(os.getenv("GEMINI_TIMEOUT", "30.0"))

# Caminhos de arquivos estáticos e bases de dados JSON
BASE_DIR: Path = Path(__file__).resolve().parent
DATA_DIR: Path = BASE_DIR / "static" / "data"
ESTADOS_FILE: Path = DATA_DIR / "estados_brasil.json"
VIAGENS_FILE: Path = DATA_DIR / "viagens.json"


def carregar_estados() -> dict[str, str]:
    """Carrega o catálogo oficial das 27 UFs do Brasil diretamente do arquivo JSON."""
    with open(ESTADOS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# Mapeamento oficial das 27 Unidades Federativas do Brasil carregado do JSON
ESTADOS_BRASIL: dict[str, str] = carregar_estados()
