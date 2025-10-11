import requests
import json
from src.core.auth import get_bimer_token
from src.config.settings import ALTERDATA_BASE_URL


def fetch_cost_centers():
    """
    Busca todos os Centros de Custo na API da Alterdata e retorna um dicionário {id: nome}.
    """
    token = get_bimer_token()
    url = f"{ALTERDATA_BASE_URL}/api/centros-de-custo"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        # A API pode devolver direto uma lista ou um objeto com "ListaObjetos"
        lista = data.get("ListaObjetos", data)
        centros = {cc["Identificador"]: cc["Nome"] for cc in lista}

        print(f"🏢 Total Centros de Custo: {len(centros)}")
        return centros

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erro ao buscar Centros de Custo: {e}")
        return {}
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return {}


if __name__ == "__main__":
    cc = fetch_cost_centers()
    print(json.dumps(cc, indent=2, ensure_ascii=False))    
