from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Tuple

import pandas as pd


def _result_count(
    df_result: pd.DataFrame,
    ok_status: str,
) -> Tuple[int, int]:
    if (
        df_result is None
        or df_result.empty
        or "status" not in df_result.columns
    ):
        return 0, 0

    success = int((df_result["status"] == ok_status).sum())
    error = int((df_result["status"] == "error").sum())

    return success, error


def build_df_execution_summary(
    pipeline_start_ts: float,
    df_create_result: pd.DataFrame,
    df_delete_duplicate_result: pd.DataFrame,
    df_orfaos: pd.DataFrame,
    df_delete_orphan_result: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    create_success, create_error = _result_count(
        df_create_result,
        "created",
    )

    rows.append(
        {
            "ACTION": "CREATE MONDAY ITEMS",
            "PLANNED": (
                len(df_create_result)
                if df_create_result is not None
                else 0
            ),
            "SUCCESS": create_success,
            "ERROR": create_error,
        }
    )

    duplicate_success, duplicate_error = _result_count(
        df_delete_duplicate_result,
        "deleted",
    )

    rows.append(
        {
            "ACTION": "DELETE DUPLICATES",
            "PLANNED": (
                len(df_delete_duplicate_result)
                if df_delete_duplicate_result is not None
                else 0
            ),
            "SUCCESS": duplicate_success,
            "ERROR": duplicate_error,
        }
    )

    orphan_success, orphan_error = _result_count(
        df_delete_orphan_result,
        "deleted",
    )

    rows.append(
        {
            "ACTION": "DELETE ORPHANS",
            "PLANNED": (
                len(df_orfaos)
                if df_orfaos is not None
                else 0
            ),
            "SUCCESS": orphan_success,
            "ERROR": orphan_error,
        }
    )

    df_summary = pd.DataFrame(rows).reset_index(drop=True)
    df_summary.insert(0, "STEP", range(len(df_summary)))

    elapsed_seconds = int(time.time() - pipeline_start_ts)
    duration_text = (
        f"{elapsed_seconds // 60}m "
        f"{elapsed_seconds % 60}s"
    )

    df_summary = pd.concat(
        [
            df_summary,
            pd.DataFrame(
                [
                    {
                        "STEP": len(df_summary),
                        "ACTION": "PIPELINE DURATION",
                        "PLANNED": duration_text,
                        "SUCCESS": "",
                        "ERROR": "",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    return df_summary


def _df_to_records(
    df_value: pd.DataFrame,
) -> List[Dict[str, Any]]:
    if df_value is None or df_value.empty:
        return []

    df_safe = (
        df_value
        .astype(object)
        .where(pd.notnull(df_value), None)
    )

    return df_safe.to_dict(orient="records")


def _to_number(value: Any) -> int:
    if value in (None, ""):
        return 0

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _find_by_action(
    records: List[Dict[str, Any]],
    action: str,
) -> Dict[str, Any]:
    return next(
        (
            item
            for item in records
            if item.get("ACTION") == action
        ),
        {},
    )


def _get_action_metric(
    records: List[Dict[str, Any]],
    action: str,
    metric: str,
) -> int:
    item = _find_by_action(records, action)
    return _to_number(item.get(metric))


def build_summary_payload(
    resumo: Dict[str, Any],
    df_execution_summary: pd.DataFrame,
) -> Dict[str, Any]:
    execution_summary = _df_to_records(
        df_execution_summary
    )

    execution_rows = [
        item
        for item in execution_summary
        if item.get("ACTION") != "PIPELINE DURATION"
    ]

    pipeline_duration = _find_by_action(
        execution_summary,
        "PIPELINE DURATION",
    ).get("PLANNED", "")

    return {
        "pipeline": "conterp_paid_sync",
        **resumo,
        "execution_summary": execution_summary,

        "create_monday_items_planned": _get_action_metric(
            execution_summary,
            "CREATE MONDAY ITEMS",
            "PLANNED",
        ),
        "create_monday_items_success": _get_action_metric(
            execution_summary,
            "CREATE MONDAY ITEMS",
            "SUCCESS",
        ),
        "create_monday_items_error": _get_action_metric(
            execution_summary,
            "CREATE MONDAY ITEMS",
            "ERROR",
        ),

        "delete_duplicates_planned": _get_action_metric(
            execution_summary,
            "DELETE DUPLICATES",
            "PLANNED",
        ),
        "delete_duplicates_success": _get_action_metric(
            execution_summary,
            "DELETE DUPLICATES",
            "SUCCESS",
        ),
        "delete_duplicates_error": _get_action_metric(
            execution_summary,
            "DELETE DUPLICATES",
            "ERROR",
        ),

        "delete_orphans_planned": _get_action_metric(
            execution_summary,
            "DELETE ORPHANS",
            "PLANNED",
        ),
        "delete_orphans_success": _get_action_metric(
            execution_summary,
            "DELETE ORPHANS",
            "SUCCESS",
        ),
        "delete_orphans_error": _get_action_metric(
            execution_summary,
            "DELETE ORPHANS",
            "ERROR",
        ),

        "pipeline_duration": pipeline_duration,

        "execution_total_planned": sum(
            _to_number(item.get("PLANNED"))
            for item in execution_rows
        ),
        "execution_total_success": sum(
            _to_number(item.get("SUCCESS"))
            for item in execution_rows
        ),
        "execution_total_error": sum(
            _to_number(item.get("ERROR"))
            for item in execution_rows
        ),
        "execution_has_error": any(
            _to_number(item.get("ERROR")) > 0
            for item in execution_rows
        ),
    }


if __name__ == "__main__":
    from src.webhook.send_summary_to_n8n import (
        send_summary_to_n8n,
    )

    df_execution_summary_test = pd.DataFrame(
        [
            {
                "STEP": 0,
                "ACTION": "CREATE MONDAY ITEMS",
                "PLANNED": 5,
                "SUCCESS": 0,
                "ERROR": 5,
            },
            {
                "STEP": 1,
                "ACTION": "DELETE DUPLICATES",
                "PLANNED": 0,
                "SUCCESS": 0,
                "ERROR": 0,
            },
            {
                "STEP": 2,
                "ACTION": "DELETE ORPHANS",
                "PLANNED": 0,
                "SUCCESS": 0,
                "ERROR": 0,
            },
            {
                "STEP": 3,
                "ACTION": "PIPELINE DURATION",
                "PLANNED": "7m 14s",
                "SUCCESS": "",
                "ERROR": "",
            },
        ]
    )

    resumo_test = {
        "timestamp": pd.Timestamp.now(
            tz="America/Sao_Paulo"
        ).isoformat(),
        "status": "success_with_errors",
        "alterdata_total": 39343,
        "pagamentos_semestre": 828,
        "monday_total_antes": 823,
        "novos_identificados": 5,
        "novos_enriquecidos": 5,
        "novos_criados": 0,
        "orfaos_encontrados": 0,
        "monday_total_depois": 823,
        "test_mode": True,
    }

    print(
        "\n📌 Resumo estruturado da execução "
        "(TESTE DO WEBHOOK):"
    )
    print(
        df_execution_summary_test.to_string(
            index=False
        )
    )

    payload = build_summary_payload(
        resumo=resumo_test,
        df_execution_summary=(
            df_execution_summary_test
        ),
    )

    print("\n📦 Payload JSON do teste:")
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )

    send_summary_to_n8n(payload)