import json
from src.config.settings import (
    check_required_envs,
    MONDAY_GROUP_PADRAO,
    MONDAY_GROUP_MOVBCO,
)
from src.core.fetch_cost_centers import fetch_cost_centers
from src.core.fetch_alterdata import fetch_all_titles
from src.utils.date_filters import filter_by_current_semester
from src.core.fetch_monday import fetch_monday_ids
from src.core.compare_ids import find_new_ids, find_monday_orphans
from src.core.fetch_details import enrich_titles
from src.core.create_items_monday import enviar_para_monday
from src.core.delete_items_monday import delete_duplicate_items, delete_monday_orphan_items


def main():
    print("\n🚀 Iniciando automação CONTERP PAID SYNC\n")

    # 1️⃣ Verifica variáveis de ambiente
    check_required_envs()

    # 2️⃣ Busca Centros de Custo
    print("\n🏢 Buscando Centros de Custo...")
    cc = fetch_cost_centers()
    primeiros_5 = dict(list(cc.items())[:5])
    print(json.dumps(primeiros_5, indent=2, ensure_ascii=False))

    # 3️⃣ Busca títulos pagos da Alterdata
    print("\n💰 Buscando Pagamentos Realizados no Alterdata...")
    df_alterdata = fetch_all_titles()
    print(df_alterdata)

    if df_alterdata.empty:
        print("⚠️ Nenhum dado retornado da Alterdata. Encerrando execução.")
        return

    # 4️⃣ Filtra títulos pelo semestre atual
    print("\n📆 Filtrando Pagamentos do Semestre Atual...")
    df_semestre = filter_by_current_semester(df_alterdata)
    print(df_semestre)

    if df_semestre.empty:
        print("⚠️ Nenhum título dentro do semestre atual. Encerrando execução.")
        return

    # 5️⃣ Busca IDs do Monday (estado inicial)
    print("\n📊 Buscando IDs existentes no Monday...")
    df_monday = fetch_monday_ids()
    print(df_monday)

    # 6️⃣ Compara e encontra novos IDs
    print("\n🔍 Comparando Alterdata x Monday...")
    new_ids = find_new_ids(df_semestre, df_monday)
    print(new_ids)

    # 7️⃣ Enriquece Novos ID's
    print("\n📥 Enriquecendo Novos Pagamentos...")
    df_enriquecido = enrich_titles(new_ids, cc)

    if df_enriquecido.empty:
        print("⚠️ Nenhum pagamento foi enriquecido.")
    else:
        print(f"\n📊 Total de Pagamentos enriquecidos: {len(df_enriquecido)}")

        # 🔹 Converter colunas de data para string no formato "YYYY-MM-DD"
        for col in ["Data de Cadastro", "Dt. venc. original", "Dt. da Realização"]:
            if col in df_enriquecido.columns:
                df_enriquecido[col] = df_enriquecido[col].dt.strftime("%Y-%m-%d")

        # 🔹 Converte o DataFrame inteiro para JSON formatado
        df_enr_json = df_enriquecido.to_json(orient="records", indent=2, force_ascii=False)

        print("\n🧾 Dados enriquecidos dos Novos Pagamentos:")
        print(df_enr_json)

    # 8️⃣ Envia os novos títulos pro Monday
    print("\n🚀 Enviando novos títulos para o Monday...")
    enviar_para_monday(df_enriquecido)

    # 9️⃣ Pós-processamento de segurança: limpeza de duplicados
    print("\n🧹 Verificando e limpando duplicados no Monday...")
    try:
        delete_duplicate_items()
        print("✅ Limpeza de duplicados concluída com sucesso.")
    except Exception as e:
        print(f"⚠️ Falha ao executar limpeza de duplicados: {e}")

    # 🔄 Recarrega o estado do Monday após inserções e limpeza de duplicados
    print("\n🔄 Atualizando estado do Monday após inserções/limpeza...")
    df_monday_final = fetch_monday_ids()
    print(df_monday_final)

    # 1️⃣0️⃣ Remoção de 'órfãos' no final (coerência total com Alterdata do semestre)
    print("\n🧹 Removendo 'órfãos' do Monday (escopo: grupos sincronizados)...")

    df_orfaos = find_monday_orphans(df_semestre, df_monday_final)
    print(f"👻 Órfãos encontrados: {len(df_orfaos)}")
    
    if not df_orfaos.empty:
        delete_monday_orphan_items(df_orfaos)

    print("\n🏁 Execução concluída com sucesso!")


if __name__ == "__main__":
    main()
