# 💸 Conterp Paid Sync

> Integração automatizada entre **Alterdata (Bimer)** e **Monday.com** para sincronizar pagamentos realizados com eficiência, confiabilidade e rastreabilidade.

---

## 🚀 Visão geral

O **Conterp Paid Sync** elimina o retrabalho manual na conciliação de **Pagamentos Realizados** entre o Bimer da **Alterdata** e o **Monday.com**.

A automação coleta, trata e sincroniza os pagamentos, mantendo os dados atualizados e registrando o resultado de cada execução no **Apache Airflow**.

---

## 🧠 Principais recursos

- 🔄 Sincronização de Pagamentos Realizados do **Alterdata (Bimer)** para o **Monday.com**
- 🧾 Tratamento de grupos, status e colunas do board
- 🧹 Remoção de duplicidades por ID e itens órfãos
- 📊 Resumo estruturado com itens planejados, processados e com erro
- 🧰 Configuração por variáveis de ambiente
- 📈 Progresso em tempo real com `tqdm`
- 🐳 Execução isolada com Docker
- 🌬️ Orquestração e monitoramento pelo Apache Airflow
- 💬 Envio do resumo ao **n8n** e notificação pelo **WhatsApp**
- 🧩 Arquitetura modular e extensível
- 🔁 Processamento idempotente

---

## 🧩 Estrutura do projeto

### Itens na raiz do repositório

```text
conterp-paid-sync/
├── .env.example
├── .dockerignore
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── src/
```

### Árvore principal do `src/`

```text
src/
├── main.py
├── config/
│   └── settings.py
├── core/
│   ├── auth.py
│   ├── fetch_cost_centers.py
│   ├── fetch_alterdata.py
│   ├── fetch_details.py
│   ├── fetch_monday.py
│   ├── compare_ids.py
│   ├── create_items_monday.py
│   ├── delete_items_monday.py
│   └── summary/
│       └── build_execution_summary.py
├── webhook/
│   └── # Envio do resumo da execução ao n8n
└── utils/
    ├── date_filters.py
    └── detect_duplicates_monday.py
```

### Responsabilidades principais

- `main.py`: executa o pipeline completo.
- `create_items_monday.py`: cria novos pagamentos no Monday e retorna o resultado de cada item.
- `delete_items_monday.py`: remove duplicidades e itens órfãos.
- `build_execution_summary.py`: consolida sucessos, erros e duração do pipeline.
- `webhook/`: envia o resumo estruturado ao n8n.

---

## ⚙️ Configuração

### 1. Clone o repositório

```bash
git clone git@github.com:Conterp/conterp-paid-sync.git
cd conterp-paid-sync
```

### 2. Configure o `.env`

```bash
cp .env.example .env
```

Exemplo:

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

# Monitoramento
N8N_WEBHOOK_URL=https://seu-endereco-n8n/webhook/conterp-paid-sync
```

> O arquivo `.env` não deve ser versionado e já está incluído no `.gitignore` e no `.dockerignore`.

---

## 🧭 Execução

### Desenvolvimento

```bash
docker compose up --build
```

### Build da imagem em produção

```bash
docker compose build --no-cache
```

Imagem gerada:

```text
conterp-paid-sync-app:latest
```

### Execução direta

```bash
docker run --rm \
  --env-file /opt/automations/conterp-paid-sync/.env \
  conterp-paid-sync-app:latest
```

---

## 🌬️ Execução pelo Apache Airflow

A automação é executada pelo Airflow por meio da DAG:

```text
conterp_paid_sync
```

Arquivo da DAG:

```text
conterp_paid_sync_dag.py
```

Task:

```text
run_conterp_paid_sync_pipeline
```

Os logs de cada execução ficam disponíveis diretamente na interface do Airflow.

---

## 💬 Integração com n8n e WhatsApp

Ao final do pipeline, o sistema gera um resumo contendo:

- itens planejados para criação;
- itens criados com sucesso;
- erros de criação;
- duplicidades removidas;
- itens órfãos removidos;
- duração total;
- status geral da execução.

O resumo é enviado ao **n8n**, que processa os dados e encaminha a notificação pelo **WhatsApp**.

Erros individuais são registrados no resumo sem interromper todo o processamento. Erros fatais encerram a execução com falha.

---

## ⏰ Agendamento

A DAG é executada de **segunda a sábado**, nos seguintes horários:

```text
04:00
10:00
19:00
```

Expressão cron utilizada pelo Airflow:

```cron
0 4,10,19 * * 1-6
```

Timezone:

```text
America/Sao_Paulo
```

O Airflow está configurado com:

- `catchup=False`
- uma tentativa adicional em caso de falha;
- intervalo de 10 minutos entre tentativas;
- apenas uma execução ativa da DAG por vez.

---

## 🔒 Segurança

- Credenciais isoladas no arquivo `.env`
- `.env` excluído da imagem Docker
- Execução conteinerizada
- Logs centralizados no Airflow
- Webhook configurado por variável de ambiente
- Nenhum segredo incluído no código-fonte
- Resumo enviado ao n8n sem exposição de credenciais

---

## 🤝 Autor

**João Carser**  
[github.com/JoaoCarser](https://github.com/JoaoCarser)
