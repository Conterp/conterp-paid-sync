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
│   └── main.py              # Ponto de entrada
│
├── Dockerfile               # Imagem da automação
├── docker-compose.yml       # Orquestra execução do container
├── run.sh                   # Script agendado pelo cron (gera logs com data)
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
git clone git@github.com:JoaoCarser/conterp-paid-sync.git
cd conterp-paid-sync
```

### 2. Configure o `.env`
Copie o arquivo de exemplo:
```bash
cp .env.example .env
```
Preencha com suas credenciais da **Alterdata** e da **Monday.com**.

> 💡 Tokens de API são sensíveis — o `.env` já está no `.gitignore`.

---

## 🧭 Execução

### 🔹 Localmente (modo desenvolvimento)
```bash
docker compose up
```

### 🔹 Em produção (AWS EC2)
O script `run.sh` executa o container e salva os logs automaticamente:

```bash
/opt/automations/conterp-paid-sync/run.sh
```

Os logs ficam em:
```
/opt/automations/conterp-paid-sync/logs/
```

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

## 🧰 Requisitos

| Dependência | Versão mínima |
|--------------|----------------|
| Docker       | 24+ |
| Docker Compose | plugin ativo |
| Python       | 3.12 (na imagem base) |

Instalação local (opcional):
```bash
pip install -r requirements.txt
```

---

## 🔒 Segurança

- Credenciais seguras via `.env`
- Execução isolada em container
- Logs centralizados e versionados por data

---

## 🤝 Autor

**João Carser**  
