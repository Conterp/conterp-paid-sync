from typing import Any, Dict

import requests

from src.config.settings import (
    N8N_WEBHOOK_TIMEOUT,
    N8N_WEBHOOK_URL,
)


def send_summary_to_n8n(summary: Dict[str, Any]) -> int:
    """
    Envia ao n8n o resumo estruturado gerado pelo main.py.

    Retorna o status HTTP da resposta.
    Gera erro quando o envio falhar para que o Airflow identifique a falha.
    """
    if not isinstance(summary, dict):
        raise TypeError(
            "O resumo enviado ao n8n deve ser um dicionário."
        )

    if not summary:
        raise ValueError(
            "O resumo enviado ao n8n não pode estar vazio."
        )

    print("\n🔗 Enviando resumo da execução ao n8n...")

    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=summary,
            timeout=N8N_WEBHOOK_TIMEOUT,
        )
        response.raise_for_status()

    except requests.RequestException as exc:
        raise RuntimeError(
            f"Falha ao enviar resumo ao n8n: {exc}"
        ) from exc

    print(f"✅ Resumo enviado ao n8n: HTTP {response.status_code}")
    return response.status_code


def send_to_n8n(summary: Dict[str, Any]) -> int:
    """
    Mantém compatibilidade com o nome usado anteriormente.
    """
    return send_summary_to_n8n(summary)