# Módulo de Inteligência Artificial Gemini & Fallback (Guia Turístico e Culinária)

import concurrent.futures
import re
from typing import Any

from google import genai
from google.genai.errors import APIError

from config import GEMINI_KEY, GEMINI_TIMEOUT

# Modelo exigido no enunciado primeiro; os demais só entram se ele falhar.
MODELOS_GEMINI: tuple[str, ...] = ("gemini-3.6-flash", "gemini-3.5-flash", "gemini-2.5-flash")

# ==============================================================================
# 👤 RESPONSABILIDADE DO ALUNO 2: Inteligência Artificial (Gemini AI) & Fallback
# ==============================================================================


def limpar_formato_texto(texto: str) -> str:
    """Remove marcações residuais de markdown (** ou *), hashtags, crases e saudações, mantendo apenas emojis."""
    texto = re.sub(r"```(?:text|markdown)?", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"^[ \t]*[*-][ \t]+", "• ", texto, flags=re.MULTILINE)  # bullets viram "•"
    texto = re.sub(r"[*#`]", "", texto)
    texto = re.sub(r"^\s*(olá|ola|oi)\b[^\n]*[,:!]\s*", "", texto, flags=re.IGNORECASE)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


def _montar_prompt(destino: str, contexto: str) -> str:
    linha_contexto = (
        f"Contexto real desta viagem (use nas seções de clima e dicas da viagem): {contexto}\n" if contexto else ""
    )
    return (
        f"Você é um guia turístico brasileiro experiente. Escreva um guia DETALHADO e específico "
        f"para o destino {destino}. O nome exato do destino deve aparecer no título e nas recomendações.\n"
        f"{linha_contexto}"
        "Use EXATAMENTE estas seções, nesta ordem, com o título em maiúsculas na própria linha:\n"
        "📍 GUIA DE <DESTINO>\n"
        "🏛️ PONTOS TURÍSTICOS PRINCIPAIS (4 a 6 itens; cada linha começa com 📍, traz o nome do local, "
        "dois pontos e 1 a 2 frases dizendo o que fazer lá e o melhor momento para visitar)\n"
        "🍲 CULINÁRIA LOCAL (3 a 5 itens; cada linha começa com 🍽️, traz o prato ou doce típico, dois pontos "
        "e uma frase sobre ingredientes ou onde experimentar)\n"
        "🎭 CULTURA E EVENTOS (2 a 3 linhas começando com 🎉: festas, feiras ou tradições locais)\n"
        "🌦️ MELHOR ÉPOCA E CLIMA (1 a 2 frases)\n"
        "🚗 DICAS PARA A VIAGEM (2 a 3 linhas começando com 🧭, aproveitando distância, tempo e paradas do contexto)\n"
        "💡 DICA DE OURO (1 dica prática e pouco óbvia)\n"
        "Regras: use somente texto puro e emojis, sem Markdown, asteriscos, hashtags ou saudações. "
        "Não use frases genéricas como 'os principais pontos da região' e não troque o destino por outra cidade. "
        "Se não tiver certeza de um nome próprio, descreva o tipo de atração sem inventar nomes."
    )


def _guia_fallback(destino: str, contexto: str = "") -> str:
    texto = (
        f"📍 GUIA DE {destino.upper()}\n"
        "🏛️ PONTOS TURÍSTICOS PRINCIPAIS\n"
        f"📍 Pesquise e visite os pontos históricos, culturais e naturais de {destino}.\n\n"
        "🍲 CULINÁRIA LOCAL\n"
        f"🍽️ Experimente pratos típicos e prestigie restaurantes locais de {destino}.\n\n"
        "🎭 CULTURA E EVENTOS\n"
        f"🎉 Consulte a agenda de festas, feiras e tradições locais de {destino}.\n\n"
        "🌦️ MELHOR ÉPOCA E CLIMA\n"
        f"Verifique a previsão do tempo e a melhor época para visitar {destino}.\n\n"
    )
    if contexto:
        texto += f"🚗 DICAS PARA A VIAGEM\n🧭 {contexto}\n\n"
    return texto + (
        "💡 DICA DE OURO\n"
        f"Confira o clima e os horários de funcionamento antes de visitar {destino}."
    )


def obter_guia_destino_com_diagnostico(destino: str, contexto: str = "") -> tuple[str, dict[str, Any]]:
    """Invoca o modelo Gemini com limite operacional (GEMINI_TIMEOUT, padrão 30.0s; o enunciado cita 6.0s) em ThreadPoolExecutor.

    `contexto` é opcional: clima, distância e paradas reais da viagem, para deixar o guia mais detalhado.
    Em caso de timeout, chave inválida ou ausência de cota, aciona automaticamente
    o gerador de contingência com roteiro estruturado em texto puro com emojis.
    Retorna a tupla (texto_guia, diagnostico_metadados).
    """
    diagnostico: dict[str, Any] = {
        "status": "fallback", "modelo": MODELOS_GEMINI[0], "fallback_utilizado": True, "mensagem": ""
    }
    if not GEMINI_KEY:
        diagnostico["mensagem"] = "Chave Gemini ausente"
        return _guia_fallback(destino, contexto), diagnostico

    def gerar() -> tuple[str, str]:
        cliente = genai.Client(api_key=GEMINI_KEY)
        prompt = _montar_prompt(destino, contexto)
        ultimo_erro: APIError | None = None
        for modelo in MODELOS_GEMINI:
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
        texto, modelo = futuro.result(timeout=GEMINI_TIMEOUT)
        diagnostico.update({"status": "sucesso", "modelo": modelo, "fallback_utilizado": False})
        return texto, diagnostico
    except Exception as erro:  # noqa: BLE001 - qualquer falha (rede, chave, cota, timeout) vira fallback, nunca HTTP 500
        futuro.cancel()
        diagnostico["mensagem"] = str(erro)[:200] or "Tempo limite excedido"
        return _guia_fallback(destino, contexto), diagnostico
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def obter_guia_destino(destino: str) -> str:
    """Wrapper utilitário que retorna apenas o texto do guia."""
    texto, _ = obter_guia_destino_com_diagnostico(destino)
    return texto
