import os

# ===========================
# 🔐 Configurações Alterdata
# ===========================
ALTERDATA_USER = os.getenv("ALTERDATA_USER")
ALTERDATA_PASS = os.getenv("ALTERDATA_PASS")
ALTERDATA_BASE_URL = os.getenv("ALTERDATA_BASE_URL")
# ===========================
# 🔐 Configurações Monday.com
# ===========================
MONDAY_BASE_URL = os.getenv("MONDAY_BASE_URL")
MONDAY_API_TOKEN = os.getenv("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = os.getenv("MONDAY_BOARD_ID")
MONDAY_COLUMN_ID = os.getenv("MONDAY_COLUMN_ID")

# Agora cada grupo é separado
MONDAY_GROUP_PADRAO = os.getenv("MONDAY_GROUP_PADRAO")
MONDAY_GROUP_MOVBCO = os.getenv("MONDAY_GROUP_MOVBCO")


# ===========================
# 🔍 Validação opcional
# ===========================
def check_required_envs():
    missing = [
        var for var in [
            "ALTERDATA_USER",
            "ALTERDATA_PASS",
            "ALTERDATA_BASE_URL",
            "MONDAY_API_TOKEN",
            "MONDAY_BOARD_ID",
            "MONDAY_BASE_URL"
        ] if not globals().get(var)
    ]
    if missing:
        print(f"⚠️ Atenção: variáveis ausentes no .env → {', '.join(missing)}")
    else:
        print("✅ Todas as variáveis de ambiente carregadas corretamente.")

if __name__ == "__main__":
    # Teste rápido: python src/config/settings.py
    check_required_envs()
