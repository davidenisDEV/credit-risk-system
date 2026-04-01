import json
import time
import os
import pika
import pandas as pd
from datetime import datetime
from pydantic import BaseModel, ValidationError
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# ==========================================
# 1. CONFIGURAÇÕES DE BANCO DE DADOS
# ==========================================
# Conecta usando o nome do container 'postgres' e as credenciais do docker-compose
DB_URL = "postgresql://admin:admin_password@postgres:5432/risk_database"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Tabela no Banco de Dados
class TransactionRecord(Base):
    __tablename__ = "transactions"
    
    transaction_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, index=True)
    amount = Column(Float)
    merchant_category = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ==========================================
# 2. REGRAS DE NEGÓCIO E CONTRATO
# ==========================================
class Transaction(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    merchant_category: str

def analyze_risk(df: pd.DataFrame) -> str:
    """Motor de regras (Pandas)"""
    amount = df['amount'].iloc[0]
    if amount > 1000:
        return "REJEITADO (Valor Suspeito)"
    return "APROVADO"

# ==========================================
# 3. CONSUMIDOR DA FILA
# ==========================================
def callback(ch, method, properties, body):
    db = SessionLocal()
    try:
        raw_data = json.loads(body)
        transaction = Transaction(**raw_data)
        
        exists = db.query(TransactionRecord).filter(TransactionRecord.transaction_id == transaction.transaction_id).first()
        if exists:
            print(f"[!] IDEMPOTÊNCIA: Transação {transaction.transaction_id} já processada anteriormente. Ignorando.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

       
        print(f"\n[-] Analisando transação: {transaction.transaction_id}...")
        df = pd.DataFrame([transaction.model_dump()])
        status = analyze_risk(df)
        
        # --- SALVANDO NO BANCO DE DADOS ---
        new_record = TransactionRecord(
            transaction_id=transaction.transaction_id,
            user_id=transaction.user_id,
            amount=transaction.amount,
            merchant_category=transaction.merchant_category,
            status=status
        )
        db.add(new_record)
        db.commit()
        
        print(f"[✓] Transação {transaction.transaction_id} | Status: {status} | Salva no BD.")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except ValidationError:
        print(f"[x] Erro de Validação. Descartando.")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        print(f"[x] Erro Interno: {str(e)}")
        db.rollback()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    finally:
        db.close()

def main():
    connection = None
    for i in range(5):
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='credit_queue', port=5672))
            break
        except pika.exceptions.AMQPConnectionError:
            print(f"Aguardando RabbitMQ... (Tentativa {i+1}/5)")
            time.sleep(5)
            
    if not connection:
        raise Exception("Falha crítica ao conectar ao RabbitMQ.")

    channel = connection.channel()
    channel.queue_declare(queue='transaction_queue', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='transaction_queue', on_message_callback=callback)

    print('🚀 Motor de Risco (Python) conectado ao Postgres. Aguardando transações...')
    channel.start_consuming()

if __name__ == '__main__':
    main()
