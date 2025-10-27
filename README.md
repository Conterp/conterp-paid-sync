# 💸 Conterp Paid Sync

> Integração automatizada entre **Alterdata (Bimer)** e **Monday.com**, para sincronizar pagamentos e lançamentos financeiros com eficiência, confiabilidade e rastreabilidade.

---

## 🚀 Visão geral

O **Conterp Paid Sync** elimina o retrabalho manual na conciliação de **Pagamentos Realizados** entre o Bimer da **Alterdata** e a **Monday.com**.  
A automação coleta, trata e sincroniza os pagamentos de forma segura, garantindo **dados atualizados**, **logs rastreáveis** e **execuções agendadas em produção**.

---

## 🧠 Principais recursos

- 🔄 **Sincronização automatizada** de Pagamentos Realizados do **Alterdata (Bimer)** para **Monday.com**  
- 🧾 **Tratamento inteligente** dos lançamentos (grupos, status e colunas do board)  
- 🧰 **Configuração simples** via `.env`  
- 📊 **Progresso em tempo real** com `tqdm`  
- 🐳 **Execução isolada com Docker**  
- ⏰ **Agendamento via cron** (produção em AWS/EC2)  
- 💬 **Envio automático de relatórios** ao Email via **n8n**  
- 🧩 **Arquitetura modular e extensível**  
- 🧹 **Higiene de dados no Monday**: remoção de **duplicidades por ID** e exclusão de **itens órfãos** a cada execução, garantindo **idempotência**

---

## 🧩 Estrutura do projeto

### Itens na **raiz** do repositório

```
conterp-paid-sync/
├── .env.example          # Exemplo de variáveis de ambiente
├── .gitignore
├── Dockerfile            # Imagem da automação (python:3.12-slim)
├── docker-compose.yml    # Orquestra a execução do container
├── requirements.txt      # Dependências
├── README.md
├── logs/                 # (gerado em runtime) diretório de logs por execução
└── src/                  # Código-fonte principal
```

### Árvore do `src/`

```
src/
├── main.py                      # Ponto de entrada (pipeline fim-a-fim)
├── config/
│   └── settings.py              # Carrega .env e valida variáveis
├── core/
│   ├── auth.py                  # Login no Bimer (token)
│   ├── fetch_cost_centers.py    # Centros de Custo (id→nome)
│   ├── fetch_alterdata.py       # Títulos baixados (paginado + retry + paralelo)
│   ├── fetch_details.py         # Detalhes de um título (enriquecimento)
│   ├── fetch_monday.py          # Leitura GraphQL (paginada por cursor)
│   ├── compare_ids.py           # Novos (A∖M) e órfãos (M∖A)
│   ├── create_items_monday.py   # Criação de itens (GraphQL)
│   └── delete_items_monday.py   # Remoção de duplicados e órfãos
├── postprocess/
│   └── send_log_to_n8n.py       # 📤 Resumo de log → n8n → Email
└── utils/
    ├── date_filters.py          # Intervalo do semestre atual + filtro
    └── detect_duplicates_monday.py # Diagnóstico de duplicidade (board)
```

> 🗂️ Observação: `logs/` fica **fora** de `src/` e guarda um arquivo por execução (nomeado por data/hora).

---

## ⚙️ Configuração

### 1) Clone o repositório
```bash
git clone git@github.com:Conterp/conterp-paid-sync.git
cd conterp-paid-sync
```

### 2) Configure o `.env`
Copie o exemplo:
```bash
cp .env.example .env
```

Preencha com suas credenciais da **Alterdata**, **Monday.com** e o **webhook do n8n** (exemplo ilustrativo):
```env
# Alterdata / Bimer
ALTERDATA_USER=seu.usuario
ALTERDATA_PASS=sua.senha
ALTERDATA_BASE_URL=https://xxxxbimerapi.alterdata.cloud

# Monday.com
MONDAY_BASE_URL=https://api.monday.com/v2
MONDAY_API_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxx
MONDAY_BOARD_ID=1234567890
MONDAY_COLUMN_ID=coluna_id_primaria
MONDAY_GROUP_PADRAO=group_default
MONDAY_GROUP_MOVBCO=group_movbco

# Observabilidade (opcional)
N8N_WEBHOOK_URL=https://seu-endereco-n8n/webhook/conterp-paid-sync
```

> 💡 O `.env` já está no `.gitignore`.

---

## 🧭 Execução

### 🔹 Local (desenvolvimento)
```bash
docker compose up --build
```

### 🔹 Produção (AWS EC2)
Use um script (ex.: `run.sh`) para executar, gerar logs e enviar o resumo ao **n8n**.  
Exemplo de caminho no servidor:
```
/opt/automations/conterp-paid-sync/run.sh
```

Logs gerados em:
```
/opt/automations/conterp-paid-sync/logs/
```

---

## 🧰 Exemplo de `run.sh.example`

> Modelo para testes locais (ajuste paths conforme seu ambiente).

```bash
#!/bin/bash
# Caminho base
cd /opt/automations/conterp-paid-sync

# Timezone Brasil
export TZ="America/Sao_Paulo"

# Nome do log (data/hora)
LOG_FILE="logs/cron_$(date '+%Y-%m-%d_%H-%M').log"

# Executa e salva log
/usr/bin/docker compose up --build --abort-on-container-exit > "$LOG_FILE" 2>&1

echo "📤 Enviando resumo do log para o n8n..."

docker run --rm   -v /workspaces/conterp-paid-sync/logs:/app/logs   -v /workspaces/conterp-paid-sync/src:/app   --env-file /workspaces/conterp-paid-sync/.env   -e LOG_PATH="/app/logs/teste_envio.log"   -w /app python:3.12-slim /bin/bash -c   "pip install requests python-dotenv >/dev/null 2>&1 && python -m postprocess.send_log_to_n8n"

echo '✅ Log enviado com sucesso!'
```

> 🧠 Em produção, use os caminhos reais do EC2 (`/opt/automations/...`).

---

## 💬 Integração com n8n e Email

Ao fim da execução, o **Conterp Paid Sync** envia um resumo do log ao **n8n**, que formata e encaminha ao **Email** (UX por **JAMI**).  
Exemplo de mensagem:

```
Tudo pronto por aqui 🚀

📅 14/10/2025 às 19:18
💼 Pagamentos no Monday
• Antes: 4070
• Depois: 4106 (+36)
• Duplicados removidos: 0

📊 Grupos:
• Pagamentos: 36
• MOVBCO: 0

🧾 Total Alterdata (semestre): 4106
Processo finalizado com sucesso 🌟 Sistemas 100% alinhados.
```

---

## ⏰ Agendamento (cron)

Exemplo de agenda na EC2:

```
# Segunda a sexta: 04:00, 10:30 e 19:00
0 4 * * 1-5 /opt/automations/conterp-paid-sync/run.sh
30 10 * * 1-5 /opt/automations/conterp-paid-sync/run.sh
0 19 * * 1-5 /opt/automations/conterp-paid-sync/run.sh

# Sábado: 10:30
30 10 * * 6 /opt/automations/conterp-paid-sync/run.sh
```

Cada execução gera um log nomeado por data/hora, por exemplo:
```
logs/cron_2025-10-13_04-00.log
```

---

## 🔒 Segurança

- Credenciais isoladas via `.env`  
- Execução conteinerizada (Docker)  
- Logs organizados por execução (sem dados sensíveis)  
- Resumo de logs enviado ao n8n (sem vazar segredos)

---

## 🤝 Autor

**João Carser**  
[github.com/JoaoCarser](https://github.com/JoaoCarser)
