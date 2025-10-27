import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config.settings import ALTERDATA_USER, ALTERDATA_PASS, ALTERDATA_BASE_URL


def get_bimer_token():
    """
    Faz login na API da Alterdata (Bimer) e retorna o access_token.
    Implementa retry automático e backoff exponencial.
    """
    url = f"{ALTERDATA_BASE_URL}/auth/token"
    payload = {
        "username": ALTERDATA_USER,
        "password": ALTERDATA_PASS
    }

    # 🔁 Configuração de retry apenas para POST
    retry = Retry(
        total=5,  # número máximo de tentativas
        backoff_factor=1,  # tempo entre tentativas (1s, 2s, 4s, 8s, etc)
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],  # apenas POST, já que é login
        respect_retry_after_header=True,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        response = session.post(url, data=payload, timeout=30)  # timeout maior e retry ativo
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Erro de conexão com Alterdata: {e}")

    try:
        data = response.json()
    except ValueError:
        raise ValueError("Resposta inválida da API (não é JSON).")

    token = data.get("accessToken")
    if not token:
        raise ValueError("Token não encontrado na resposta da API.")

    print("🔓 Login na Alterdata efetuado com sucesso!")
    return token


if __name__ == "__main__":
    # Teste rápido (opcional)
    token = get_bimer_token()
    print(f"Token obtido (parcial): {token[:20]}...")
