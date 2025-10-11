import requests
from src.config.settings import ALTERDATA_USER, ALTERDATA_PASS, ALTERDATA_BASE_URL

def get_bimer_token():
    """
    Faz login na API da Alterdata (Bimer) e retorna o access_token.
    """
    url = f"{ALTERDATA_BASE_URL}/auth/token"
    payload = {
        "username": ALTERDATA_USER,
        "password": ALTERDATA_PASS
    }

    try:
        response = requests.post(url, data=payload, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Erro de conexão com Alterdata: {e}")

    data = response.json()
    token = data.get("accessToken")
    if not token:
        raise ValueError("Token não encontrado na resposta da API.")

    print("🔓 Login na Alterdata efetuado com sucesso!")
    return token

if __name__ == "__main__":
    # Teste rápido (opcional)
    token = get_bimer_token()
    print(f"Token obtido (parcial): {token[:20]}...")
