# Base leve com Python 3.12
FROM python:3.12-slim

# Pasta de trabalho dentro do container
WORKDIR /app

# Copia dependências e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código
COPY . .

# Configura ambiente Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Comando de inicialização
CMD ["bash", "-c", "python -u -m src.main | tee /app/logs/conterp-paid-sync.log"]
