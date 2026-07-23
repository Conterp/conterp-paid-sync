import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from src.config.settings import check_required_envs
from src.core.fetch_cost_centers import fetch_cost_centers
from src.core.fetch_alterdata import fetch_all_titles
from src.utils.date_filters import filter_by_current_semester
from src.core.fetch_monday import fetch_monday_ids
from src.core.compare_ids import find_new_ids, find_monday_orphans
from src.core.fetch_details import enrich_titles
from src.core.create_items_monday import enviar_para_monday
from src.core.delete_items_monday import (
    delete_duplicate_items,
    delete_monday_orphan_items,
)
from src.core.summary.build_execution_summary import (
    build_df_execution_summary,
    build_summary_payload,
)
from src.webhook.send_summary_to_n8n import send_summary_to_n8n


TIMEZONE = ZoneInfo("America/Sao_Paulo")


def main():
    pipeline_start_ts = time.time()
    execution_failed = False

    df_create_result = pd.DataFrame()
    df_delete_duplicate_result = pd.DataFrame()
    df_orfaos = pd.DataFrame()
    df_delete_orphan_result = pd.DataFrame()

    resumo = {
        "timestamp": datetime.now(TIMEZONE).isoformat(
            timespec="seconds"
        ),
        "status": "running",
        "alterdata_total": 0,
        "pagamentos_semestre": 0,
        "monday_total_antes": 0,
        "novos_identificados": 0,
        "novos_enriquecidos": 0,
        "novos_criados": 0,
        "orfaos_encontrados": 0,
        "monday_total_depois": 0,
    }

    print("\n🚀 Iniciando automação CONTERP PAID SYNC\n")

    try:
        # 1️⃣ Verifica variáveis de ambiente
        check_required_envs()

        # 2️⃣ Busca Centros de Custo
        print("\n🏢 Buscando Centros de Custo...")
        cc = fetch_cost_centers()
        primeiros_5 = dict(list(cc.items())[:5])
        print(
            json.dumps(
                primeiros_5,
                indent=2,
                ensure_ascii=False,
            )
        )

        # 3️⃣ Busca títulos pagos da Alterdata
        print(
            "\n💰 Buscando Pagamentos Realizados "
            "no Alterdata..."
        )
        df_alterdata = fetch_all_titles()
        resumo["alterdata_total"] = len(df_alterdata)
        print(df_alterdata)

        if df_alterdata.empty:
            resumo["status"] = "success_no_alterdata_data"
            print(
                "⚠️ Nenhum dado retornado da Alterdata. "
                "Encerrando execução."
            )
            return resumo

        # 4️⃣ Filtra títulos pelo semestre atual
        print(
            "\n📆 Filtrando Pagamentos do Semestre Atual..."
        )
        df_semestre = filter_by_current_semester(
            df_alterdata
        )
        resumo["pagamentos_semestre"] = len(df_semestre)
        print(df_semestre)

        if df_semestre.empty:
            resumo["status"] = "success_no_semester_data"
            print(
                "⚠️ Nenhum título dentro do semestre atual. "
                "Encerrando execução."
            )
            return resumo

        # 5️⃣ Busca IDs do Monday — estado inicial
        print(
            "\n📊 Buscando IDs existentes no Monday..."
        )
        df_monday = fetch_monday_ids()
        resumo["monday_total_antes"] = len(df_monday)
        print(df_monday)

        # 6️⃣ Compara e encontra novos IDs
        print(
            "\n🔍 Comparando Alterdata x Monday..."
        )
        new_ids = find_new_ids(
            df_semestre,
            df_monday,
        )
        resumo["novos_identificados"] = len(new_ids)
        print(new_ids)

        # 7️⃣ Enriquece novos IDs
        print(
            "\n📥 Enriquecendo Novos Pagamentos..."
        )
        df_enriquecido = enrich_titles(
            new_ids,
            cc,
        )
        resumo["novos_enriquecidos"] = len(
            df_enriquecido
        )

        if df_enriquecido.empty:
            print(
                "⚠️ Nenhum pagamento foi enriquecido."
            )
        else:
            print(
                f"\n📊 Total de Pagamentos enriquecidos: "
                f"{len(df_enriquecido)}"
            )

            # Converte colunas de data para YYYY-MM-DD
            for col in [
                "Data de Cadastro",
                "Dt. venc. original",
                "Dt. da Realização",
            ]:
                if col in df_enriquecido.columns:
                    df_enriquecido[col] = (
                        df_enriquecido[col]
                        .dt.strftime("%Y-%m-%d")
                    )

            df_enr_json = df_enriquecido.to_json(
                orient="records",
                indent=2,
                force_ascii=False,
            )

            print(
                "\n🧾 Dados enriquecidos dos "
                "Novos Pagamentos:"
            )
            print(df_enr_json)

        # 8️⃣ Envia os novos títulos para o Monday
        print(
            "\n🚀 Enviando novos títulos para o Monday..."
        )
        df_create_result = enviar_para_monday(
            df_enriquecido
        )

        if (
            not df_create_result.empty
            and "status" in df_create_result.columns
        ):
            resumo["novos_criados"] = int(
                (
                    df_create_result["status"]
                    == "created"
                ).sum()
            )

        # 9️⃣ Pós-processamento: limpeza de duplicados
        print(
            "\n🧹 Verificando e limpando "
            "duplicados no Monday..."
        )
        df_delete_duplicate_result = (
            delete_duplicate_items()
        )
        print(
            "✅ Limpeza de duplicados concluída."
        )

        # Recarrega o Monday após inserções e duplicados
        print(
            "\n🔄 Atualizando estado do Monday "
            "após inserções/limpeza..."
        )
        df_monday_atualizado = fetch_monday_ids()
        print(df_monday_atualizado)

        # 🔟 Remove órfãos do Monday
        print(
            "\n🧹 Removendo 'órfãos' do Monday "
            "(escopo: grupos sincronizados)..."
        )
        df_orfaos = find_monday_orphans(
            df_semestre,
            df_monday_atualizado,
        )
        resumo["orfaos_encontrados"] = len(
            df_orfaos
        )
        print(
            f"👻 Órfãos encontrados: "
            f"{len(df_orfaos)}"
        )

        if not df_orfaos.empty:
            df_delete_orphan_result = (
                delete_monday_orphan_items(
                    df_orfaos
                )
            )

        # Confirma o estado final real do Monday
        print(
            "\n🔄 Confirmando estado final do Monday..."
        )
        df_monday_final = fetch_monday_ids()
        resumo["monday_total_depois"] = len(
            df_monday_final
        )

        resumo["status"] = "success"
        print(
            "\n🏁 Execução concluída com sucesso!"
        )
        return resumo

    except Exception as exc:
        execution_failed = True
        resumo["status"] = "error"
        resumo["error_type"] = type(exc).__name__
        resumo["error_message"] = str(exc)

        print(
            f"\n❌ Execução encerrada com erro: "
            f"{type(exc).__name__}: {exc}"
        )
        raise

    finally:
        df_summary = build_df_execution_summary(
            pipeline_start_ts=pipeline_start_ts,
            df_create_result=df_create_result,
            df_delete_duplicate_result=(
                df_delete_duplicate_result
            ),
            df_orfaos=df_orfaos,
            df_delete_orphan_result=(
                df_delete_orphan_result
            ),
        )

        if not execution_failed:
            action_rows = df_summary[
                df_summary["ACTION"]
                != "PIPELINE DURATION"
            ]

            total_errors = int(
                pd.to_numeric(
                    action_rows["ERROR"],
                    errors="coerce",
                )
                .fillna(0)
                .sum()
            )

            if (
                resumo["status"] == "success"
                and total_errors > 0
            ):
                resumo["status"] = "success_with_errors"

        print(
            "\n📌 Resumo estruturado da execução:"
        )
        print(
            df_summary.to_string(index=False)
        )

        if not execution_failed:
            summary_payload = build_summary_payload(
                resumo=resumo,
                df_execution_summary=df_summary,
            )
            send_summary_to_n8n(
                summary_payload
            )


if __name__ == "__main__":
    main()
