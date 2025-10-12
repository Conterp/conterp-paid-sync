# 💸 Conterp Paid Sync

> Integração automatizada entre **Alterdata (Bimer)** e **Monday.com**, para sincronizar pagamentos e lançamentos financeiros com eficiência, confiabilidade e rastreabilidade.

---

## 🚀 Visão geral

O **Conterp Paid Sync** foi desenvolvido para eliminar o retrabalho manual na conciliação de dados financeiros entre o Bimer da **Alterdata** e o ecossistema de gestão da **Monday.com**.  
Ele coleta, trata e sincroniza informações de forma segura, garantindo **dados atualizados**, **logs claros** e **operações idempotentes** (sem duplicidade).

---

## 🧠 Principais recursos

- 🔄 **Sincronização bidirecional** entre Alterdata e Monday  
- 🧾 **Tratamento inteligente de lançamentos** (por grupos, status)  
- 🧰 **Configuração simplificada** via `.env`  
- 📊 **Feedback em tempo real** com `tqdm` (barra de progresso)  
- 🧩 **Arquitetura modular e extensível**  
- 🧪 **Testes automatizados** com `pytest`  

---

## 🧩 Estrutura do projeto

```
conterp-paid-sync/
├── .env.example # Exemplo de variáveis de ambiente
├── requirements.txt # Dependências principais e de desenvolvimento
├── src/ # Código-fonte principal
│ ├── config/ # Configurações globais e variáveis do sistema
│ │ ├── init.py
│ │ └── settings.py
│ │
│ ├── core/ # Lógica central de sincronização
│ │ ├── init.py
│ │ ├── auth.py # Autenticação e tokens
│ │ ├── compare_ids.py # Comparação de registros Alterdata × Monday
│ │ ├── create_items_monday.py # Criação de itens no Monday
│ │ ├── fetch_alterdata.py # Busca de dados da API Alterdata
│ │ ├── fetch_cost_centers.py # Coleta de centros de custo
│ │ ├── fetch_details.py # Detalhamento e normalização de dados
│ │ └── fetch_monday.py # Comunicação com a API Monday.com
│ │
│ ├── utils/ # Funções auxiliares e utilitários
│ │ ├── init.py
│ │ └── date_filters.py # Filtros e formatação de datas
│ │
│ └── main.py # Ponto de entrada da aplicação
│
├── .gitignore # Regras de exclusão do Git
└── README.md # Documentação principal
```

---

## ⚙️ Configuração

### 1. Clone o repositório
```bash
git clone git@github.com:JoaoCarser/conterp-paid-sync.git
cd conterp-paid-sync
```

### 2. Crie e configure o `.env`
Copie o arquivo de exemplo:
```bash
cp .env.example .env
```
Preencha com suas credenciais da **Alterdata** e da **Monday.com**.

> 💡 Dica UX: tokens de API são sensíveis. Evite versionar o `.env` — ele já está ignorado no `.gitignore`.

---

## 🧭 Execução

### Via Python diretamente
```bash
python src/main.py
```

### Monitorar progresso
A barra de progresso (`tqdm`) mostrará o status de sincronização em tempo real.

---

## 🧰 Requisitos

| Dependência | Versão mínima |
|--------------|----------------|
| Python       | 3.9+ |
| requests     | latest |
| pandas       | latest |
| python-dotenv | latest |

Instale todas as dependências com:
```bash
pip install -r requirements.txt
```

---

## 🔒 Segurança

- Nunca exponha suas credenciais da Alterdata ou Monday.com.
- As variáveis sensíveis são carregadas via `.env`.
- O script valida chaves antes da execução.

---

## 🤝 Autor

João Carser
