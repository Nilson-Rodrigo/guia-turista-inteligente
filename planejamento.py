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
        f"Pesquise e visite os pontos históricos, culturais e naturais de {destino}.\n\n"
        "🍲 CULINÁRIA LOCAL\n"
        f"Experimente pratos típicos e prestigie restaurantes locais de {destino}.\n\n"
        "💡 DICA DE OURO\n"
        f"Confira o clima e os horários de funcionamento antes de visitar {destino}."
    )


def obter_guia_destino_com_diagnostico(destino: str) -> tuple[str, dict[str, Any]]:
    """Invoca o modelo Gemini com limite operacional de 30.0s em ThreadPoolExecutor.

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

    def gerar() -> tuple[str, str]:
        cliente = genai.Client(api_key=GEMINI_KEY)
        prompt = (
            f"Você é um guia turístico local. Escreva um guia curto e específico para o destino "
            f"{destino}. O nome exato do destino deve aparecer no título e nas recomendações. "
            "Diga o que o viajante pode fazer lá: cite atrações, bairros, espaços culturais, "
            "paisagens, atividades ao ar livre ou eventos que existam nesse destino e indique "
            "comidas típicas associadas à cidade ou ao estado. "
            "Não use frases genéricas como 'os principais pontos da região' e não troque "
            "o destino por outra cidade. Se não tiver certeza de um nome, descreva o tipo "
            "de atração sem inventar nomes. Inclua as seções Atrações, Gastronomia e Dica de ouro. "
            "Use somente texto puro e emojis, sem Markdown, asteriscos ou saudações."
        )
        ultimo_erro: APIError | None = None
        for modelo in ("gemini-2.5-flash", "gemini-3.5-flash", "gemini-3.6-flash"):
            try:
                resposta = cliente.models.generate_content(model=modelo, contents=prompt)
                texto = limpar_formato_texto(str(resposta.text or ""))
                if texto:
                    return texto, modelo
            except APIError as erro:
                ultimo_erro = erro
        if ultimo_erro:
            raise ultimo_erro
        raise ValueError("Resposta vazia")

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    futuro = executor.submit(gerar)
    try:
        texto, modelo = futuro.result(timeout=30.0)
        diagnostico.update({"status": "sucesso", "modelo": modelo, "fallback_utilizado": False})
        return texto, diagnostico
    except (APIError, RuntimeError, TimeoutError, ValueError, OSError) as erro:
        futuro.cancel()
        diagnostico["mensagem"] = str(erro)[:200] or "Tempo limite excedido"
        return _guia_fallback(destino), diagnostico
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def obter_guia_destino(destino: str) -> str:
    """Wrapper utilitário que retorna apenas o texto do guia."""
    texto, _ = obter_guia_destino_com_diagnostico(destino)
    return texto
