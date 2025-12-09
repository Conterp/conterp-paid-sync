import requests
import pandas as pd
import re
from tqdm import tqdm
from json import JSONDecodeError
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.auth import get_bimer_token
from src.config.settings import ALTERDATA_BASE_URL


# ==========================
# ⚙️ Sessão HTTP com retry
# ==========================
def build_session(token: str, max_retries: int = 5, backoff_factor: float = 2.0) -> requests.Session:
    retry = Retry(
        total=max_retries,
        connect=max_retries,
        read=max_retries,
        status=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504, 524],
        allowed_methods=["GET"],
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=30, pool_maxsize=30)
    s = requests.Session()
    s.mount("https://", adapter)
    s.headers.update({"Authorization": f"Bearer {token}"})
    return s


# ==========================
# 🔍 Função para 1 título
# ==========================
def get_title_details(session: requests.Session, titulo_id: str, dict_cc: dict):
    url = f"{ALTERDATA_BASE_URL}/api/titulosAPagar/{titulo_id}"

    try:
        r = session.get(url, timeout=(30, 30))
        r.raise_for_status()
        data = r.json()
    except (requests.exceptions.RequestException, JSONDecodeError):
        return None

    lista = data.get("ListaObjetos", [])
    if not lista:
        return None

    obj = lista[0]

    # ---- Centros de custo ----
    centros = []
    for item in obj.get("Itens", []):
        centros.extend(item.get("CentrosDeCusto", []) or [])

    nomes_cc = [dict_cc.get(cc.get("IdentificadorCentroDeCusto")) for cc in centros if cc.get("IdentificadorCentroDeCusto")]
    nome_cc_final = (
        None if not nomes_cc else
        nomes_cc[0] if len(set(nomes_cc)) == 1 else
        "Diversos centros de custo"
    )

    # ---- Observação e AF/RQ ----
    observacao = obj.get("Observacao", "") or ""
    
    # Procura AF ou RQ seguidos de número
    match = re.search(r"\b(?:AF|RQ)\s*(\d+)\b", observacao, re.IGNORECASE)

    # Se encontrou, pega só o número (grupo 1)
    af_number = match.group(1) if match else "Sem AF"

    # ---- Campos principais ----
    data_baixa = obj.get("DataBaixa")
    if not data_baixa or (isinstance(data_baixa, str) and data_baixa.startswith("0001")):
        return None

    return {
        "Numero af": af_number,
        "Nome da pessoa": obj.get("Descricao"),
        "Nome curto": " ".join((obj.get("Descricao") or "").split()[:2]),
        "Data de Cadastro": pd.to_datetime(obj.get("DataCadastro"), errors="coerce"),
        "Dt. venc. original": pd.to_datetime(obj.get("DataVencimento"), errors="coerce"),
        "Dt. da Realização": pd.to_datetime(data_baixa, errors="coerce"),
        "Vl. título (atualizado)": obj.get("Valor"),
        "Vl. líquido": obj.get("ValorBaixado"),
        "Forma de Pagamento": (obj.get("FormaPagamento") or {}).get("Nome"),
        "Centro(s) de custo": nome_cc_final,
        "Nº Título": obj.get("Numero"),
        "Vl. desconto desmembramento": round((obj.get("DesmembramentoDesconto") or {}).get("Valor", 0), 2),
        "Vl. PIS x COFINS x CSLL": round((obj.get("DesmembramentoPisCofinsCsll") or {}).get("Valor", 0), 2),
        "Vl. IRRF": round((obj.get("DesmembramentoIRRF") or {}).get("Valor", 0), 2),
        "Vl. INSS": round((obj.get("DesmembramentoINSS") or {}).get("Valor", 0), 2),
        "Vl. ISS": round((obj.get("DesmembramentoISS") or {}).get("Valor", 0), 2),
        "Vl. multa desmembramento": round((obj.get("DesmembramentoMulta") or {}).get("Valor", 0), 2),
        "Vl. juros desmembramento": round((obj.get("DesmembramentoJuros") or {}).get("Valor", 0), 2),
        "Observação": (obj.get("SituacaoAdministrativa") or {}).get("Nome"),
        "TIPO DE OPERAÇÃO": (obj.get("FormaPagamento") or {}).get("TipoFormaPagamento"),
        "ID": obj.get("Identificador"),
    }


# ==========================
# 🚀 Função principal
# ==========================
def enrich_titles(df_novos_ids: pd.DataFrame, df_cost_centers):
    """
    Enriquecer os novos títulos com os dados completos da Alterdata.
    Aceita tanto dict quanto DataFrame de centros de custo.
    """
    if df_novos_ids.empty:
        print("⚠️ Nenhum novo ID para enriquecer.")
        return pd.DataFrame()

    # 🔹 Compatível com dict ou DataFrame
    if isinstance(df_cost_centers, dict):
        dict_cc = df_cost_centers
    else:
        dict_cc = dict(zip(df_cost_centers["ID"], df_cost_centers["NomeCentroCusto"]))

    token = get_bimer_token()
    session = build_session(token)

    registros = []
    ids = df_novos_ids["ID"].dropna().unique().tolist()

    print(f"\n📥 Buscando detalhes de {len(ids)} novos títulos na Alterdata...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_title_details, session, id_, dict_cc): id_ for id_ in ids}
        for fut in tqdm(as_completed(futures), total=len(futures), desc="🔍 Enriquecendo", unit="título"):
            registro = fut.result()
            if registro:
                registros.append(registro)

    df_enriquecido = pd.DataFrame(registros)

    return df_enriquecido
