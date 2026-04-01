# 🛡️ Distributed Credit Risk Engine for Microtransactions

Um sistema distribuído, assíncrono e de alta disponibilidade projetado para avaliar o risco de microtransações em tempo real, sem impactar a latência da jornada do usuário final.

## 🧠 O Problema que Este Sistema Resolve

Em ambientes de alto volume (como marketplaces de games, apps de delivery ou gateways de pagamento), o processo de checkout é o momento mais crítico. 
Se a API de pagamento for síncrona e tentar calcular fraudes, checar histórico no banco de dados e validar regras complexas no momento do clique, duas coisas acontecem:
1. **Alta Latência:** O usuário fica olhando para uma tela de carregamento (aumentando a taxa de abandono de carrinho).
2. **Queda em Picos de Acesso:** Em uma "Black Friday" ou lançamento de um jogo, o banco de dados recebe milhares de consultas simultâneas e derruba o sistema inteiro (Gargalo de I/O).

**A Solução:** Desacoplamento através de uma arquitetura orientada a eventos (Event-Driven Architecture).

---

## 🏗️ Decisões de Engenharia e Arquitetura (ADR)

Este projeto não utiliza uma stack única por acaso. Cada tecnologia foi escolhida para resolver um problema específico do pipeline de dados:

### 1. Ingestão de Dados com Go (Fiber)
* O "Recepcionista".
* **Por que Go?** Golang possui uma gestão de concorrência (Goroutines) incrivelmente leve. A API em Go não processa regras de negócio; ela apenas valida o payload e "enfileira" o pedido em milissegundos, retornando um `202 Accepted` para o cliente. Isso garante que a API não caia mesmo sob ataques ou picos extremos de tráfego.

### 2. Mensageria com RabbitMQ
* O "Amortecedor" (Buffer).
* **Por que RabbitMQ?** Ele atua como um *Message Broker* que absorve os picos de requisição. Se a API receber 10.000 transações em 1 segundo, o banco de dados não será bombardeado. As mensagens ficam seguras na fila, esperando que os workers tenham capacidade de processá-las no seu próprio ritmo.

### 3. Motor de Regras com Python (Pandas/Pydantic)
* O "Cérebro".
* **Por que Python?** Embora Go seja rápido para rede, Python é o rei da análise de dados. Usamos **Pydantic** para garantir contratos de dados estritos (se o JSON mudar, a aplicação não quebra, ela rejeita graciosamente). Usamos **Pandas** para facilitar a futura injeção de modelos de Machine Learning (como Isolation Forests para detecção de anomalias).

### 4. Persistência e Idempotência (PostgreSQL + SQLAlchemy)
* A "Fonte da Verdade".
* **O Diferencial Técnico:** Em sistemas distribuídos, uma mensagem pode ser entregue duas vezes (queda de rede, timeout). O sistema implementa **Idempotência**: antes de salvar ou processar um risco, o worker consulta o banco. Se a transação (`transaction_id`) já existir, ela é descartada. Isso evita dupla cobrança e corrupção de dados.

### 5. Observabilidade de Negócio com Streamlit
* Os "Olhos" da operação.
* **Por que?** Código rodando no terminal não gera valor visual para stakeholders. O dashboard consome os dados processados e entrega métricas vitais em tempo real (Taxa de Rejeição, Volume Financeiro, Distribuição de Fraudes), fechando o ciclo do dado.

---

## 💼 Aplicações Reais e Valor de Negócio

Os conceitos aplicados nesta arquitetura são a base de sistemas em grandes empresas de tecnologia. Esta mesma esteira (Ingestão Rápida -> Fila -> Worker Analítico -> Dashboard) pode ser adaptada para solucionar diversos problemas do mercado:

* **Fintechs & Bancos:** Processamento de transferências PIX, validação de KYC (Know Your Customer) assíncrona, cálculo de limite de crédito dinâmico.
* **E-commerce & Varejo:** Processamento de pedidos (separação de estoque, emissão de nota fiscal em background), motores de recomendação de produtos em tempo real.
* **IoT (Internet das Coisas):** Ingestão de milhões de logs de sensores industriais por segundo (via Go), enfileiramento e detecção de falhas de maquinário (via Python) antes de salvar no banco de dados.
* **Saúde (Healthtech):** Triagem automática de exames laboratoriais, onde a API recebe o exame e um worker Python aplica regras de urgência antes de alertar um médico.

---

## 🚀 Conceitos Sêniores Demonstrados neste Repositório
- **Desacoplamento de Microsserviços**
- **Processamento Assíncrono e Message Queuing (QoS, ACK/NACK)**
- **Resiliência a Falhas e Idempotência**
- **Containerização e Orquestração Local (Docker Compose)**
- **Data Validation & Type Hinting Strict (Pydantic)**
- **Data Visualization & Business Intelligence**
