FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema operacional necessárias para compilar libs como Pandas e Psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc

# Copia os requirements e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código do worker
COPY worker.py .

# O parâmetro -u (unbuffered) é crucial no Docker com Python para os 'prints' aparecerem em tempo real no log
CMD ["python", "-u", "worker.py"]