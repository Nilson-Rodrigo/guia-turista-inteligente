# Serviços de integração com APIs externas (Google OAuth, Open-Meteo e OSRM)

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
    client: httpx.Client, cidade: str, uf: str = ""
) -> tuple[float, float, str]:
    """Consulta o Open-Meteo Geocoding com filtro Brasil (country_codes=BR) e timeout=4.0s.

    Retorna a tupla (latitude, longitude, nome_formatado). Caso a busca falhe,
    aplica fallback seguro retornando (0.0, 0.0, "Cidade - UF").
    """
    uf_normalizada = uf.strip().upper()
    fallback_lat_lon = CAPITAIS_BRASIL.get(uf_normalizada, (0.0, 0.0))
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
    escolhido = next(
        (item for item in resultados if obter_sigla_uf(str(item.get("admin1", "")), uf) == uf),
        resultados[0],
    )
    detectada = obter_sigla_uf(str(escolhido.get("admin1", "")), uf)
    try:
        return float(escolhido["latitude"]), float(escolhido["longitude"]), detectada
    except (KeyError, TypeError, ValueError):
        return fallback


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
        rota = resposta.json().get("routes", [])[0]
        minutos = round(float(rota["duration"]) / 60)
        horas, minutos = divmod(minutos, 60)
        tempo = f"{horas}h {minutos:02d}min de carro" if horas else f"{minutos}min de carro"
        return {"distancia": f"{float(rota['distance']) / 1000:.1f} km", "tempo": tempo, "modal": "carro"}
    except (httpx.HTTPError, IndexError, KeyError, TypeError, ValueError):
        return fallback
