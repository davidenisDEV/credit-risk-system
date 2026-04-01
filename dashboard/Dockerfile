FROM python:3.11-slim

WORKDIR /app

# Dependência do SO para o psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8501

# Comando padrão do Streamlit configurado para rodar no Docker
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]