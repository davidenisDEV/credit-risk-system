FROM golang:1.21-alpine

WORKDIR /app

# Inicializamos o módulo e baixamos as dependências por aqui
RUN go mod init credit-risk-api
RUN go get github.com/gofiber/fiber/v2
RUN go get github.com/streadway/amqp

# Copiamos o nosso código
COPY main.go .

# Compilamos o binário
RUN go build -o api-go main.go

# Expomos a porta da API
EXPOSE 8080

# Comando para rodar a aplicação
CMD ["./api-go"]