package main

import (
	"log"

	"github.com/gofiber/fiber/v2"
	"github.com/streadway/amqp"
)

func main() {
	app := fiber.New()

	// 1. Conectando ao RabbitMQ (usamos o nome do container 'credit_queue' definido no docker-compose)
	conn, err := amqp.Dial("amqp://guest:guest@credit_queue:5672/")
	if err != nil {
		log.Fatalf("Falha ao conectar no RabbitMQ: %v", err)
	}
	defer conn.Close()

	ch, err := conn.Channel()
	if err != nil {
		log.Fatalf("Falha ao abrir o canal: %v", err)
	}
	defer ch.Close()

	// 2. Declarando a fila (garante que ela exista antes de enviarmos algo)
	q, err := ch.QueueDeclare(
		"transaction_queue", // nome da fila
		true,                // durable (sobrevive a quedas do RabbitMQ)
		false,               // delete when unused
		false,               // exclusive
		false,               // no-wait
		nil,                 // arguments
	)
	if err != nil {
		log.Fatalf("Falha ao declarar a fila: %v", err)
	}

	// 3. Rota POST para receber as transações
	app.Post("/v1/transaction", func(c *fiber.Ctx) error {

		// Publica o JSON recebido diretamente na fila do RabbitMQ
		err = ch.Publish(
			"",     // exchange
			q.Name, // routing key (nome da fila)
			false,  // mandatory
			false,  // immediate
			amqp.Publishing{
				ContentType: "application/json",
				Body:        c.Body(),
			})

		if err != nil {
			return c.Status(500).JSON(fiber.Map{"erro": "Falha ao enviar para a fila"})
		}

		// Retorna 202 Accepted (Significa: Recebido, mas será processado de forma assíncrona)
		return c.Status(202).JSON(fiber.Map{
			"status": "Transação recebida e na fila para análise de risco",
		})
	})

	log.Println("🚀 API Go rodando na porta 8080...")
	log.Fatal(app.Listen(":8080"))
}
