import json
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


class KafkaTextProcessor:
    def __init__(self, consume_topic: str, produce_topic: str, bootstrap_servers: str, group_id: str, model):
        self.consume_topic = consume_topic
        self.produce_topic = produce_topic
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = None
        self.producer = None
        self.model = model

    async def start(self):
        loop = asyncio.get_running_loop()

        self.consumer = AIOKafkaConsumer(
            self.consume_topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            enable_auto_commit=True,
            loop=loop,
        )
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            loop=loop,
        )

        await self.consumer.start()
        await self.producer.start()
        print(f"Consumer started for topic: {self.consume_topic}")
        print(f"Producer initialized for topic: {self.produce_topic}")

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
        if self.producer:
            await self.producer.stop()
        print("Consumer and producer stopped.")

    async def send_to_producer(self, result: dict):
        try:
            message = json.dumps(result).encode("utf-8")
            await self.producer.send_and_wait(
                topic=self.produce_topic,
                value=message,
            )
            print(f"Message sent to topic {self.produce_topic}: {result}")
        except Exception as e:
            print(f"Error sending message to producer: {e}")

    async def process_messages(self):
        try:
            async for message in self.consumer:
                try:
                    input_data = json.loads(message.value.decode("utf-8"))
                    text = input_data.get("text", "")
                    print(f"Received message: {input_data}")

                    prediction = self.model.predict(text)
                    result = {
                        "original_text": text,
                        "prediction": prediction,
                        "metadata": {"source_offset": message.offset},
                    }
                    print(f"Processed result: {result}")

                    await self.send_to_producer(result)
                except Exception as e:
                    print(f"Error processing message: {e}")
        except Exception as e:
            print(f"Error in consumer loop: {e}")