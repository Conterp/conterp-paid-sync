# 💸 Conterp Paid Sync

> Integração automatizada entre **Alterdata (Bimer)** e **Monday.com**, para sincronizar pagamentos e lançamentos financeiros com eficiência, confiabilidade e rastreabilidade.

---

## 🚀 Visão geral

O **Conterp Paid Sync** elimina o retrabalho manual na conciliação de **Pagamentos Realizados** entre o Bimer da **Alterdata** e a **Monday.com**.  
A automação coleta, trata e sincroniza os pagamentos de forma segura, garantindo **dados atualizados**, **logs rastreáveis** e **execuções agendadas em produção**.

---

## 🧠 Principais recursos

- 🔄 **Sincronização bidirecional** entre Alterdata e Monday  
- 🧾 **Tratamento inteligente de lançamentos** (por grupos e status)  
- 🧰 **Configuração simplificada** via `.env`  
- 📊 **Progresso em tempo real** com `tqdm`  
- 🐳 **Execução isolada com Docker**  
- ⏰ **Agendamento automático via cron (produção AWS)**  
- 💬 **Envio automático de relatórios ao Email via n8n**  
- 🧩 **Arquitetura modular e extensível**

---

## 🧩 Estrutura do projeto

```
conterp-paid-sync/
├── .env.example             # Exemplo de variáveis de ambiente
├── requirements.txt         # Dependências principais
├── src/                     # Código-fonte principal
│   ├── config/              # Configurações globais
│   ├── core/                # Lógica central de sincronização
│   ├── utils/               # Funções auxiliares
│   ├── postprocess/         # 📤 Pós-processamento (envio de logs ao n8n)
│   │   └── send_log_to_n8n.py
│   └── main.py              # Ponto de entrada
│
├── Dockerfile               # Imagem da automação
├── docker-compose.yml       # Orquestra execução do container
├── run.sh.example           # 🔹 Exemplo de execução local (modelo)
├── logs/                    # Armazena logs de cada execução
│   ├── conterp-paid-sync.log
│   └── cron_2025-10-13_01-45.log
│
└── README.md
```

---

## ⚙️ Configuração

### 1. Clone o repositório
```bash
git clone git@github.com:Conterp/conterp-paid-sync.git
cd conterp-paid-sync
```

### 2. Configure o `.env`
Copie o arquivo de exemplo:
```bash
cp .env.example .env
```

Preencha com suas credenciais da **Alterdata**, **Monday.com** e o **webhook do n8n**:

```env
N8N_WEBHOOK_URL=https://seu-endereco-n8n/webhook/conterp-paid-sync
```

> 💡 Tokens e URLs são sensíveis — o `.env` já está no `.gitignore`.

---

## 🧭 Execução

### 🔹 Localmente (modo desenvolvimento)
```bash
docker compose up
```

### 🔹 Em produção (AWS EC2)
O script `run.sh` executa o container, gera os logs e envia o resumo automaticamente ao **n8n**, que repassa para o **Email**.

```bash
/opt/automations/conterp-paid-sync/run.sh
```

Logs são salvos em:
```
/opt/automations/conterp-paid-sync/logs/
```

---

## 🧰 Exemplo de `run.sh.example`

> Este modelo mostra como configurar o script localmente para testes.

```bash
#!/bin/bash
# Caminho base da automação
cd /opt/automations/conterp-paid-sync

# Define timezone manualmente (Brasil)
export TZ="America/Sao_Paulo"

# Gera nome do log com data/hora atual
LOG_FILE="logs/cron_$(date '+%Y-%m-%d_%H-%M').log"

# Executa a automação e salva o log
/usr/bin/docker compose up --build --abort-on-container-exit > "$LOG_FILE" 2>&1

echo "📤 Enviando resumo do log para o n8n..."

docker run --rm   -v /workspaces/conterp-paid-sync/logs:/app/logs   -v /workspaces/conterp-paid-sync/src:/app   --env-file /workspaces/conterp-paid-sync/.env   -e LOG_PATH="/app/logs/teste_envio.log"   -w /app python:3.12-slim /bin/bash -c "pip install requests python-dotenv >/dev/null 2>&1 && python -m postprocess.send_log_to_n8n"

echo "✅ Log enviado com sucesso!"
```

> 🧠 **Dica:**  
> Em produção, o `run.sh` real usa caminhos do EC2 (`/opt/automations/...`),  
> mas o `.example` serve para testes locais no VS Code ou Codespaces.

---

## 💬 Integração com o n8n e Gmail

Ao final da execução, o **Conterp Paid Sync** envia um resumo do log ao **n8n**, que processa e encaminha ao **Email**, formatado pela assistente **JAMI**.

Exemplo de mensagem enviada:

```
Tudo pronto por aqui 🚀  

📅 14/10/2025 às 19:18  
💼 Pagamentos no Monday  
• Antes: *4070*  
• Depois: *4106* (+*36*)  
•  Duplicados removidos: 0

📊 Grupos:  
• Pagamentos: *36*  
• MOVBCO: *0*  

🧾 Total Alterdata (semestre): *4106*  

Processo finalizado com sucesso 🌟 Sistemas 100% alinhados.
```

> ✨ A **JAMI** aplica UX writing e formatação visual para que as mensagens sejam  
> curtas, elegantes e claras, mantendo a leitura confortável no Email.

---

## ⏰ Agendamento automático (cron)

Na EC2, o cron agenda a automação para execução recorrente:

```
# Segunda a sexta: 04:00, 10:30 e 19:00
0 4 * * 1-5 /opt/automations/conterp-paid-sync/run.sh
30 10 * * 1-5 /opt/automations/conterp-paid-sync/run.sh
0 19 * * 1-5 /opt/automations/conterp-paid-sync/run.sh

# Sábado: 10:30
30 10 * * 6 /opt/automations/conterp-paid-sync/run.sh
```

Cada execução gera um log nomeado por data/hora, ex:
```
logs/cron_2025-10-13_04-00.log
```

---

## 🔒 Segurança

- Credenciais seguras via `.env`  
- Execução isolada em container  
- Logs centralizados e versionados por data  
- Envio de informações resumidas ao n8n (sem dados sensíveis)

---

## 🤝 Autor

**João Carser**  
[github.com/JoaoCarser](https://github.com/JoaoCarser)
