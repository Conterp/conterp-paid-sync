import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.auth import get_bimer_token
from src.config.settings import ALTERDATA_BASE_URL


# ==========================
# ⚙️ Configurações padrão
# ==========================
LIMITE_POR_PAGINA = 50
MAX_WORKERS = 5


# ==========================
# 🔧 Sessão HTTP com retry
# ==========================
def build_session(token: str) -> requests.Session:
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s = requests.Session()
    s.mount("https://", adapter)
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


# ==========================
# 📡 Busca página específica
# ==========================
def fetch_page(session: requests.Session, page: int):
    url = f"{ALTERDATA_BASE_URL}/api/titulosAPagar/empresas/1"
    params = {"status": 0, "limite": LIMITE_POR_PAGINA, "pagina": page}
    r = session.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("ListaObjetos", []), data.get("Paginacao", {})


# ==========================
# 🚀 Função principal
# ==========================
def fetch_all_titles():
    """Busca todos os títulos baixados da Alterdata e retorna um DataFrame limpo."""
    token = get_bimer_token()
    session = build_session(token)

    # Primeira página pra saber quantas existem
    _, paginacao = fetch_page(session, 1)
    total_paginas = paginacao.get("TotalPagina", 1)
    total_registros = paginacao.get("Total", 0)

    print(f"📄 Total de títulos baixados: {total_registros}")
    print(f"📃 Total de páginas: {total_paginas}")

    resultados = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_page, session, p): p for p in range(1, total_paginas + 1)}
        for fut in tqdm(as_completed(futures), total=total_paginas, desc="Baixando páginas", unit="página"):
            p = futures[fut]
            try:
                lista, _ = fut.result()
                for obj in lista:
                    data_baixa = obj.get("DataBaixa")
                    if data_baixa and not data_baixa.startswith("0001"):
                        resultados.append({
                            "ID": obj["Identificador"],
                            "DataBaixa": data_baixa.split("T")[0],
                            "Pagina": p
                        })
            except Exception as e:
                print(f"⚠️ Erro na página {p}: {e}")

    df_all_titles = pd.DataFrame(resultados)
    if not df_all_titles.empty:
        df_all_titles["DataBaixa"] = pd.to_datetime(df_all_titles["DataBaixa"], errors="coerce")
        df_all_titles = df_all_titles.sort_values(by="DataBaixa", ascending=True).reset_index(drop=True)

    print(f"📜 Existem: {len(df_all_titles)} Pagamentos Realizados Baixados do Alterdata")
    return df_all_titles


# ==========================
# 🧪 Execução isolada
# ==========================
if __name__ == "__main__":
    df_all_titles = fetch_all_titles()
    print(df_all_titles)
