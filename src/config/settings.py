import os
from typing import Optional

from dotenv import load_dotenv

# Carrega as variáveis do .env (na raiz do projeto)
load_dotenv()


def _get_str(name: str) -> Optional[str]:
    """Lê uma variável string e remove espaços extras."""
    value = os.getenv(name)

    if value is None:
        return None

    value = value.strip()
    return value if value else None


def _get_required_int(name: str) -> int:
    """Lê um inteiro obrigatório, sem valor padrão."""
    value = _get_str(name)

    if value is None:
        raise RuntimeError(
            f"Variável obrigatória ausente no ambiente: {name}"
        )

    try:
        parsed_value = int(value)
    except ValueError as exc:
        raise RuntimeError(
            f"Variável {name} deve ser um número inteiro. "
            f"Valor recebido: {value!r}"
        ) from exc

    if parsed_value <= 0:
        raise RuntimeError(
            f"Variável {name} deve ser maior que zero."
        )

    return parsed_value


def _mask_secret(
    value: Optional[str],
    head: int = 4,
    tail: int = 3,
) -> str:
    """Exibe somente o início e o final de valores sensíveis."""
    if not value:
        return "MISSING"

    if len(value) <= head + tail:
        return "*" * len(value)

    return f"{value[:head]}...{value[-tail:]} (len={len(value)})"


def _preview(value: Optional[str], size: int = 30) -> str:
    """Exibe os 13 primeiros e os 5 últimos caracteres da URL."""
    if not value:
        return "MISSING"

    value = str(value)

    if len(value) <= 18:
        return "*" * len(value)

    return f"{value[:13]}...{value[-5:]}"


# ===========================
# 🔐 Configurações Alterdata
# ===========================
ALTERDATA_USER = _get_str("ALTERDATA_USER")
ALTERDATA_PASS = _get_str("ALTERDATA_PASS")
ALTERDATA_BASE_URL = _get_str("ALTERDATA_BASE_URL")

# ===========================
# 🔐 Configurações Monday.com
# ===========================
MONDAY_BASE_URL = _get_str("MONDAY_BASE_URL")
MONDAY_API_TOKEN = _get_str("MONDAY_API_TOKEN")
MONDAY_BOARD_ID = _get_str("MONDAY_BOARD_ID")
MONDAY_COLUMN_ID = _get_str("MONDAY_COLUMN_ID")

MONDAY_GROUP_PADRAO = _get_str("MONDAY_GROUP_PADRAO")
MONDAY_GROUP_MOVBCO = _get_str("MONDAY_GROUP_MOVBCO")

# ===========================
# 🔐 Configurações N8N
# ===========================
N8N_WEBHOOK_URL = _get_str("N8N_WEBHOOK_URL")
N8N_WEBHOOK_TIMEOUT = _get_required_int("N8N_WEBHOOK_TIMEOUT")


# ===========================
# 🔍 Validação obrigatória
# ===========================
def check_required_envs() -> None:
    required_envs = [
        ("ALTERDATA_USER", ALTERDATA_USER),
        ("ALTERDATA_PASS", ALTERDATA_PASS),
        ("ALTERDATA_BASE_URL", ALTERDATA_BASE_URL),
        ("MONDAY_BASE_URL", MONDAY_BASE_URL),
        ("MONDAY_API_TOKEN", MONDAY_API_TOKEN),
        ("MONDAY_BOARD_ID", MONDAY_BOARD_ID),
        ("MONDAY_COLUMN_ID", MONDAY_COLUMN_ID),
        ("MONDAY_GROUP_PADRAO", MONDAY_GROUP_PADRAO),
        ("MONDAY_GROUP_MOVBCO", MONDAY_GROUP_MOVBCO),
        ("N8N_WEBHOOK_URL", N8N_WEBHOOK_URL),
    ]

    missing = [
        name
        for name, value in required_envs
        if not value
    ]

    if missing:
        missing_lines = "\n".join(f"- {name}" for name in missing)
        raise RuntimeError(
            f"Variáveis obrigatórias ausentes:\n{missing_lines}"
        )

    print("=" * 55)
    print("✅ Configurações carregadas com sucesso".center(55))
    print("=" * 55)

    print("\n🔐 Alterdata")
    print(f"   Usuário: {ALTERDATA_USER}")
    print(f"   Senha: {_mask_secret(ALTERDATA_PASS)}")
    print(f"   URL: {_preview(ALTERDATA_BASE_URL)}")

    print("\n📊 Monday")
    print(f"   URL: {_preview(MONDAY_BASE_URL)}")
    print(f"   Token: {_mask_secret(MONDAY_API_TOKEN)}")
    print(f"   Board ID: {MONDAY_BOARD_ID}")
    print(f"   Column ID: {MONDAY_COLUMN_ID}")
    print(f"   Grupo padrão: {MONDAY_GROUP_PADRAO}")
    print(f"   Grupo MOVBCO: {MONDAY_GROUP_MOVBCO}")

    print("\n🔗 n8n")
    print(f"   Webhook: {_preview(N8N_WEBHOOK_URL)}")
    print(f"   Timeout: {N8N_WEBHOOK_TIMEOUT}s")


if __name__ == "__main__":
    # Teste rápido: python -m src.config.settings
    check_required_envs()