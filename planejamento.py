# Módulo de Inteligência Artificial Gemini & Fallback (Guia Turístico e Culinária)

import concurrent.futures
import re
from typing import Any

from google import genai
from google.genai.errors import APIError

from config import GEMINI_KEY

# ==============================================================================
# 👤 RESPONSABILIDADE DO ALUNO 2: Inteligência Artificial (Gemini AI) & Fallback
# ==============================================================================


def limpar_formato_texto(texto: str) -> str:
    """Remove marcações residuais de markdown (** ou *), hashtags, crases e saudações, mantendo apenas emojis."""
    texto = re.sub(r"```(?:text|markdown)?", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"[*#`]", "", texto)
    texto = re.sub(r"^\s*(olá|ola|oi)[^\n]*[,:!]\s*", "", texto, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def _guia_fallback(destino: str) -> str:
    return (
        f"📍 GUIA DE {destino.upper()}\n"
        "🏛️ PONTOS TURÍSTICOS PRINCIPAIS\n"
        "Visite os principais pontos históricos, culturais e naturais da região.\n\n"
        "🍲 CULINÁRIA LOCAL\n"
        "Experimente pratos típicos e prestigie restaurantes locais.\n\n"
        "💡 DICA DE OURO\n"
        "Confira o clima e os horários de funcionamento antes de sair."
    )


def obter_guia_destino_com_diagnostico(destino: str) -> tuple[str, dict[str, Any]]:
    """Invoca o modelo 'gemini-3.6-flash' com timeout de 6.0s em ThreadPoolExecutor.

    Em caso de timeout, chave inválida ou ausência de cota, aciona automaticamente
    o gerador de contingência com roteiro estruturado em texto puro com emojis.
    Retorna a tupla (texto_guia, diagnostico_metadados).
    """
    diagnostico: dict[str, Any] = {
        "status": "fallback", "modelo": "gemini-3.6-flash", "fallback_utilizado": True, "mensagem": ""
    }
    if not GEMINI_KEY:
        diagnostico["mensagem"] = "Chave Gemini ausente"
        return _guia_fallback(destino), diagnostico

    def gerar() -> str:
        cliente = genai.Client(api_key=GEMINI_KEY)
        resposta = cliente.models.generate_content(
            model="gemini-3.6-flash",
            contents=(
                f"Crie um guia turístico curto para {destino}. Inclua atrações, culinária e uma dica de ouro. "
                "Use somente texto puro e emojis, sem Markdown, asteriscos ou saudações."
            ),
        )
        return limpar_formato_texto(str(resposta.text or ""))

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            texto = executor.submit(gerar).result(timeout=6.0)
        if not texto:
            raise ValueError("Resposta vazia")
        diagnostico.update({"status": "sucesso", "fallback_utilizado": False})
        return texto, diagnostico
    except (APIError, RuntimeError, TimeoutError, ValueError, OSError) as erro:
        diagnostico["mensagem"] = str(erro)[:200]
        return _guia_fallback(destino), diagnostico


def obter_guia_destino(destino: str) -> str:
    """Wrapper utilitário que retorna apenas o texto do guia."""
    texto, _ = obter_guia_destino_com_diagnostico(destino)
    return texto
