import os
import re
import json
import requests
from config.settings import N8N_WEBHOOK_URL


def summarize_log(log_path):
    """
    Extrai dados relevantes do log da automação,
    incluindo a hora de execução do próprio log (linha 'time="..."').
    """
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Função genérica de extração
    def extract(pattern, default="0"):
        match = re.search(pattern, content)
        return match.group(1).strip() if match else default

    # 2️⃣ Se o log for JSON puro, tenta carregar direto
    if content.startswith("{") and content.endswith("}"):
        try:
            data = json.loads(content)
            data["timestamp"] = hora_execucao
            return data
        except json.JSONDecodeError:
            pass

    # 3️⃣ Extrai os demais campos relevantes
    hora_execucao = extract(r'time="([^"]+)"', default="")
    monday_total_antes = int(extract(r"Total de pagamentos localizados no Monday:\s*([0-9]+)", "0"))
    novos_pagamentos = int(extract(r"Upload concluído! (\d+) itens criados", "0"))
    grupo_pagamentos = int(extract(r"Pagamentos:\s*([0-9]+) itens", "0"))
    grupo_movbco = int(extract(r"MOVBCO:\s*([0-9]+) itens", "0"))
    pagamentos_semestre_api = int(extract(r"Total de Pagamentos no Semestre Atual:\s*([0-9]+)", "0"))

    monday_total_depois = monday_total_antes + novos_pagamentos

    # 4️⃣ Monta o resumo
    summary = {
        "timestamp": hora_execucao,
        "monday_total_antes": monday_total_antes,
        "monday_total_depois": monday_total_depois,
        "novos_pagamentos": novos_pagamentos,
        "grupo_pagamentos": grupo_pagamentos,
        "grupo_movbco": grupo_movbco,
        "pagamentos_semestre_api": pagamentos_semestre_api,
    }

    return summary


def send_to_n8n(summary):
    """Envia o resumo via webhook para o n8n"""
    n8n_url = N8N_WEBHOOK_URL
    if not n8n_url:
        print("❌ N8N_WEBHOOK_URL não configurada no .env")
        return

    try:
        res = requests.post(n8n_url, json=summary, timeout=10)
        res.raise_for_status()
        print("✅ Enviado ao n8n:", res.status_code)
    except Exception as e:
        print(f"⚠️ Falha ao enviar: {e}")


def main():
    """Pega o log mais recente e envia seu resumo ao n8n"""
    logs_dir = "/app/logs"
    log_files = [os.path.join(logs_dir, f) for f in os.listdir(logs_dir) if f.endswith(".log")]

    if not log_files:
        print("⚠️ Nenhum arquivo de log encontrado em /app/logs")
        return

    latest = sorted(log_files, key=os.path.getmtime, reverse=True)[0]
    print(f"📄 Processando log mais recente: {latest}")

    summary = summarize_log(latest)
    print("📊 Resumo extraído:", summary)

    send_to_n8n(summary)


if __name__ == "__main__":
    main()
