import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

# Configuração da página 
st.set_page_config(page_title="Risk System Dashboard", page_icon="🛡️", layout="wide")

# 1. Conexão com o Banco de Dados
DB_URL = "postgresql://admin:admin_password@postgres:5432/risk_database"

@st.cache_resource
def get_engine():
    return create_engine(DB_URL)

def load_data():
    engine = get_engine()
    query = "SELECT * FROM transactions ORDER BY created_at DESC"
    try:
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no banco: {e}")
        return pd.DataFrame()

# ==========================================
# INTERFACE DO USUÁRIO
# ==========================================
st.title("🛡️ Motor de Risco - Monitoramento em Tempo Real")
st.markdown("Acompanhamento de microtransações e detecção de anomalias/fraudes.")

col_btn, _ = st.columns([1, 5])
with col_btn:
    if st.button("🔄 Atualizar Dados"):
        st.cache_data.clear()

df = load_data()

if df.empty:
    st.info("Aguardando as primeiras transações passarem pelo pipeline (Go -> RabbitMQ -> Python -> DB)...")
else:
    # --- MÉTRICAS PRINCIPAIS ---
    total_tx = len(df)
    aprovados = len(df[df['status'] == 'APROVADO'])
    rejeitados = len(df[df['status'] != 'APROVADO'])
    taxa_rejeicao = (rejeitados / total_tx) * 100 if total_tx > 0 else 0

    st.markdown("### Visão Geral")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total de Transações", total_tx)
    col2.metric("Aprovadas ✅", aprovados)
    col3.metric("Barradas (Fraude) 🚨", rejeitados)
    col4.metric("Taxa de Bloqueio", f"{taxa_rejeicao:.1f}%")

    st.markdown("---")

    # --- GRÁFICOS ---
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.markdown("#### Distribuição de Status")
        fig1 = px.pie(
            df, names='status', hole=0.4,
            color='status',
            color_discrete_map={'APROVADO':'#00cc96', 'REJEITADO (Valor Suspeito)':'#ef553b'}
        )
        fig1.update_layout(margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig1, use_container_width=True)

    with col_graf2:
        st.markdown("#### Volume de Transações por Valor")
        fig2 = px.histogram(
            df, x='amount', color='status', 
            nbins=20, text_auto=True,
            color_discrete_map={'APROVADO':'#00cc96', 'REJEITADO (Valor Suspeito)':'#ef553b'}
        )
        fig2.update_layout(xaxis_title="Valor da Transação ($)", yaxis_title="Quantidade")
        st.plotly_chart(fig2, use_container_width=True)

    # --- TABELA DE DADOS ---
    st.markdown("### Últimas Transações Processadas")
    df_display = df.copy()
    df_display['created_at'] = pd.to_datetime(df_display['created_at']).dt.strftime('%d/%m/%Y %H:%M:%S')
    st.dataframe(df_display, use_container_width=True, hide_index=True)
