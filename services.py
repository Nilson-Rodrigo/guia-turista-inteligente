# Serviços de integração com APIs externas (Google OAuth, Open-Meteo e OSRM)

import math
import re
import unicodedata
from typing import Any

import httpx

from config import ESTADOS_BRASIL, GOOGLE_CLIENT_ID

CAPITAIS_BRASIL: dict[str, tuple[float, float]] = {
    "AC": (-9.9754, -67.8249), "AL": (-9.6658, -35.7353), "AP": (0.0349, -51.0694),
    "AM": (-3.1190, -60.0217), "BA": (-12.9777, -38.5016), "CE": (-3.7319, -38.5267),
    "DF": (-15.7939, -47.8828), "ES": (-20.3155, -40.3128), "GO": (-16.6869, -49.2648),
    "MA": (-2.5307, -44.3068), "MT": (-15.6014, -56.0979), "MS": (-20.4697, -54.6201),
    "MG": (-19.9167, -43.9345), "PA": (-1.4558, -48.4902), "PB": (-7.1195, -34.8450),
    "PR": (-25.4284, -49.2733), "PE": (-8.0476, -34.8770), "PI": (-5.0892, -42.8016),
    "RJ": (-22.9068, -43.1729), "RN": (-5.7945, -35.2110), "RS": (-30.0346, -51.2177),
    "RO": (-8.7612, -63.9004), "RR": (2.8235, -60.6758), "SC": (-27.5954, -48.5480),
    "SP": (-23.5505, -46.6333), "SE": (-10.9472, -37.0731), "TO": (-10.1840, -48.3336),
}


def _normalizar_nome_local(nome: str) -> str:
    texto = unicodedata.normalize("NFD", nome.casefold())
    texto = "".join(caractere for    caractere in texto if unicodedata.category(caractere) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", texto).strip()

def _nomes_parecidos(nome_informado: str, item: dict[str, Any]) -> bool:
    """True se o nome digitado e o nome retornado pela API se contêm (com limite de palavra)."""
    nome_api = _normalizar_nome_local(re.sub(r"\(.*?\)", "", str(item.get("name", ""))))
    if not nome_api or not nome_informado:
        return False
    if re.search(rf"\b{re.escape(nome_informado)}\b", nome_api):
        return True
    return len(nome_api) >= 5 and re.search(rf"\b{re.escape(nome_api)}\b", nome_informado) is not None


# ==============================================================================
# 👤 RESPONSABILIDADE DO ALUNO 1: APIs REST, Autenticação JWT e Geocodificação
# ==============================================================================


def verificar_token_google(client: httpx.Client, token: str) -> dict[str, Any] | None:
    """Valida o token JWT no endpoint oficial 'https://oauth2.googleapis.com/tokeninfo'.

    Verifica se o token foi emitido para o GOOGLE_CLIENT_ID configurado no projeto
    e retorna o payload do usuário (sub, name, email, picture) ou None se for inválido.
    """
    if not token:
        return None
    try:
        resposta = client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": token},
            timeout=4.0,
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except (httpx.HTTPError, ValueError):
        return None
    if dados.get("aud") != GOOGLE_CLIENT_ID or not dados.get("sub"):
        return None
    return {
        "id": str(dados["sub"]),
        "nome": str(dados.get("name", "Viajante")),
        "email": str(dados.get("email", "")),
        "foto": str(dados.get("picture", "")),
    }


def obter_sigla_uf(admin1: str, uf_informada: str = "") -> str:
    """Converte o estado retornado pela API (admin1) para a sigla oficial de 2 letras (ex: 'PI').

    Caso a API retorne um nome completo (ex: 'Piauí'), normaliza para a sigla 'PI'.
    Caso contrário, utiliza a UF informada como fallback se for válida.
    """
    uf = uf_informada.strip().upper()
    valor = re.sub(r"[^a-zA-ZÀ-ÿ ]", "", admin1).strip().casefold()
    valor_sem_acento = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", valor)
        if unicodedata.category(caractere) != "Mn"
    )
    for sigla, nome in ESTADOS_BRASIL.items():
        nome_sem_acento = "".join(
            caractere
            for caractere in unicodedata.normalize("NFD", nome.casefold())
            if unicodedata.category(caractere) != "Mn"
        )
        if valor == nome.casefold() or valor_sem_acento == nome_sem_acento or valor == sigla.casefold():
            return sigla
    return uf if uf in ESTADOS_BRASIL else ""


def buscar_coordenadas(
    client: httpx.Client, cidade: str, uf: str = "", usar_fallback_capital: bool = True
) -> tuple[float, float, str]:
    """Consulta o Open-Meteo Geocoding com filtro Brasil (country_codes=BR) e timeout=4.0s.

    Retorna a tupla (latitude, longitude, nome_formatado). Caso a busca falhe,
    aplica fallback seguro retornando (0.0, 0.0, "Cidade - UF").
    """
    uf_normalizada = uf.strip().upper()
    fallback_lat_lon = CAPITAIS_BRASIL.get(uf_normalizada, (0.0, 0.0)) if usar_fallback_capital else (0.0, 0.0)
    fallback = (*fallback_lat_lon, uf_normalizada if fallback_lat_lon != (0.0, 0.0) else "")
    try:
        resposta = client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": cidade, "count": 10, "language": "pt", "format": "json", "country_codes": "BR"},
            timeout=4.0,
        )
        resposta.raise_for_status()
        resultados = resposta.json().get("results", [])
    except (httpx.HTTPError, ValueError, TypeError):
        return fallback
    resultados = [item for item in resultados if str(item.get("country_code", "")).upper() == "BR"]
    if not resultados:
        return fallback
    resultados_uf = [
        item for item in resultados if obter_sigla_uf(str(item.get("admin1", "")), uf) == uf
    ]
    nome_informado = _normalizar_nome_local(cidade)
    # Se a UF digitada não bate com nenhum resultado, aceita a cidade de mesmo nome em outra UF
    # e devolve a UF real (admin1). Ex.: Teresina + RJ -> Teresina - PI.
    def _exatos(lista: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            item for item in lista
            if _normalizar_nome_local(re.sub(r"\(.*?\)", "", str(item.get("name", "")))) == nome_informado
        ]

    exatos_uf = _exatos(resultados_uf)
    escolhido = None
    if exatos_uf:
        escolhido = exatos_uf[0]
    elif not resultados_uf:
        # UF digitada não bate com nenhum resultado: aceita a cidade de mesmo nome em outra UF e devolve a UF
        # real (admin1). Ex.: Teresina + RJ -> Teresina - PI (teste 5 do enunciado). Se o nome existir em vários
        # estados, escolhe o mais populoso (a API ordena por relevância; em empate, vale o primeiro).
        outros = _exatos(resultados)
        escolhido = max(outros, key=lambda item: float(item.get("population") or 0)) if outros else None
    if escolhido is None:
        # Sem nome idêntico: aceita nome parecido dentro da UF informada, só se houver um único candidato
        # (ex.: "Fernando de Noronha" e a API devolveu "Noronha" ou "Arquipélago de Fernando de Noronha").
        parecidos = [item for item in resultados_uf if _nomes_parecidos(nome_informado, item)]
        escolhido = parecidos[0] if len(parecidos) == 1 else None
    if escolhido is None:
        return fallback
    detectada = obter_sigla_uf(str(escolhido.get("admin1", "")), uf)
    try:
        return float(escolhido["latitude"]), float(escolhido["longitude"]), detectada
    except (KeyError, TypeError, ValueError):
        return fallback


def destino_foi_localizado(latitude: float, longitude: float, uf_detectada: str) -> bool:
    """Indica se o geocoding encontrou o destino, sem confundir fallback com resultado real."""
    return (latitude, longitude) != CAPITAIS_BRASIL.get(uf_detectada, (0.0, 0.0)) or not uf_detectada


# ==============================================================================
# 👤 RESPONSABILIDADE DO ALUNO 2: Telemetria Climática e Roteamento Rodoviário
# ==============================================================================


def obter_clima(client: httpx.Client, lat: float, lon: float) -> dict[str, str]:
    """Consulta o Open-Meteo Forecast e retorna temperatura (°C), umidade (%) e vento (km/h).

    Caso coordenadas sejam inválidas (0.0, 0.0) ou ocorra timeout (4.0s),
    retorna dicionário de contingência com valores 'N/D'.
    """
    fallback = {"temperatura": "N/D", "umidade": "N/D", "vento": "N/D"}
    if lat == 0.0 and lon == 0.0:
        return fallback
    try:
        resposta = client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": lat, "longitude": lon, "current": "temperature_2m,relative_humidity_2m,wind_speed_10m"},
            timeout=4.0,
        )
        resposta.raise_for_status()
        atual = resposta.json()["current"]
        return {
            "temperatura": f"{float(atual['temperature_2m']):.1f} °C",
            "umidade": f"{float(atual['relative_humidity_2m']):.0f}%",
            "vento": f"{float(atual['wind_speed_10m']):.1f} km/h",
        }
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        return fallback


def obter_percurso(
    client: httpx.Client, lat_o: float, lon_o: float, lat_d: float, lon_d: float
) -> dict[str, str]:
    """Consulta o OSRM e calcula distância em km e duração de viagem de carro.

    Em caso de trajetos sem estradas (ex: ilhas) ou timeout (6.0s),
    retorna dicionário com fallback descritivo ('Sem rota direta' / 'Considere voos ou barcos').
    """
    fallback = {"distancia": "Sem rota direta", "tempo": "Considere voos ou barcos", "modal": "indisponível"}
    if (lat_o, lon_o, lat_d, lon_d) == (0.0, 0.0, 0.0, 0.0):
        return fallback
    try:
        url = f"https://router.project-osrm.org/route/v1/driving/{lon_o},{lat_o};{lon_d},{lat_d}"
        resposta = client.get(url, params={"overview": "false"}, timeout=6.0)
        resposta.raise_for_status()
        dados = resposta.json()
        if any(float(p.get("distance", 0)) > 30000 for p in dados.get("waypoints", [])):
            return fallback
        rota = dados.get("routes", [])[0]
        minutos = round(float(rota["duration"]) / 60)
        horas, minutos = divmod(minutos, 60)
        tempo = f"{horas}h {minutos:02d}min de carro" if horas else f"{minutos}min de carro"
        return {"distancia": f"{float(rota['distance']) / 1000:.1f} km", "tempo": tempo, "modal": "carro"}
    except (httpx.HTTPError, IndexError, KeyError, TypeError, ValueError):
        return fallback


def extrair_distancia_e_tempo(percurso: dict[str, str]) -> tuple[float, float] | None:
    """Converte o dict do OSRM ('1674.6 km', '21h 38min de carro') em (km, minutos).

    Retorna None quando não há rota rodoviária (fallback do OSRM).
    """
    if percurso.get("modal") != "carro":
        return None
    try:
        km = float(re.search(r"\d+(?:\.\d+)?", percurso["distancia"]).group())  # type: ignore[union-attr]
        horas = re.search(r"(\d+)\s*h", percurso["tempo"])
        minutos = re.search(r"(\d+)\s*min", percurso["tempo"])
        total_min = (int(horas.group(1)) * 60 if horas else 0) + (int(minutos.group(1)) if minutos else 0)
    except (AttributeError, KeyError, ValueError):
        return None
    return km, float(total_min)


def _formatar_duracao(minutos: float) -> str:
    horas, resto = divmod(round(minutos), 60)
    return f"{horas}h {resto:02d}min" if horas else f"{resto}min"


def calcular_gerenciador_paradas(
    distancia_total_km: float,
    tempo_total_min: float,
    capacidade_tanque_ou_bateria: float = 50.0,
    consumo_medio: float = 12.0,
    tipo_veiculo: str = "combustivel",
) -> dict[str, Any]:
    """Calcula paradas estratégicas de descanso, abastecimento/recarga e alimentação.

    Premissa obrigatória: o veículo inicia a viagem com TANQUE 100% CHEIO ou BATERIA 100% carregada.
    Considera a autonomia útil com margem de segurança de 15% (85% da autonomia máxima).
    - Abastecimento: N = floor(distancia_total / autonomia_util_km)
    - Descanso: 1 parada de 15-20 min a cada 2.5 horas (150 minutos) de percurso.
    - Alimentação: 1 parada principal (45 min) a cada 4.5 horas (270 minutos) em viagens > 4 horas.
    """
    eletrico = tipo_veiculo.strip().lower() in {"eletrico", "elétrico", "ev"}
    unidade, rotulo, acao = ("kWh", "Elétrico", "recarga") if eletrico else ("L", "Gasolina/Flex", "abastecimento")
    autonomia_maxima = capacidade_tanque_ou_bateria * consumo_medio
    autonomia_util = autonomia_maxima * 0.85
    resultado: dict[str, Any] = {
        "tanque_inicial": "100% carregada" if eletrico else "100% cheio",
        "capacidade_tanque_bateria": f"{capacidade_tanque_ou_bateria:.1f} {unidade} ({rotulo})",
        "autonomia_util_segura": f"{autonomia_util:.1f} km (Reserva 15%)",
        "paradas_abastecimento": 0,
        "paradas_descanso": 0,
        "paradas_alimentacao": 0,
        "resumo_cronograma": "Sem rota rodoviária direta: gerenciador de paradas indisponível para este trajeto.",
    }
    if distancia_total_km <= 0 or tempo_total_min <= 0 or autonomia_util <= 0:
        return resultado

    paradas_abast = math.floor(distancia_total_km / autonomia_util)
    paradas_descanso = math.floor(tempo_total_min / 150)
    # Viagens acima de 4h têm ao menos 1 refeição; depois, 1 a cada 4,5h (270 min).
    paradas_alimentacao = max(1, math.floor(tempo_total_min / 270)) if tempo_total_min > 240 else 0
    tempo_paradas = paradas_abast * 15 + paradas_descanso * 20 + paradas_alimentacao * 45

    partes = [f"Partida com {resultado['tanque_inicial']}."]
    if paradas_abast:
        marcos = ", ".join(f"km {round(autonomia_util * i)}" for i in range(1, paradas_abast + 1))
        partes.append(f"Recomenda-se {paradas_abast} {acao}(ões) ({marcos}).")
    else:
        partes.append(f"Nenhum {acao} necessário: a autonomia útil cobre o trajeto.")
    partes.append(f"{paradas_descanso} pausa(s) de descanso de 15 a 20 min (a cada 2h30 de direção).")
    if paradas_alimentacao:
        partes.append(f"{paradas_alimentacao} parada(s) de refeição principal de 45 min.")
    partes.append(
        f"Tempo estimado em paradas: {_formatar_duracao(tempo_paradas)}; "
        f"chegada total em cerca de {_formatar_duracao(tempo_total_min + tempo_paradas)}."
    )
    resultado.update(
        paradas_abastecimento=paradas_abast,
        paradas_descanso=paradas_descanso,
        paradas_alimentacao=paradas_alimentacao,
        resumo_cronograma=" ".join(partes),
    )
    return resultado
