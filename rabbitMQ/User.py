import pika
import sys
import json

class User:
    def __init__(self, username):
        self.username = username
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='direct_logs', exchange_type='direct')

        # Exclusive queue for user notifications
        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        # Bind this queue to the exchange
        self.channel.queue_bind(exchange='direct_logs', queue=self.callback_queue, routing_key=self.username)

        # Start consuming notifications from the queue
        self.channel.basic_consume(queue=self.callback_queue,
                                   on_message_callback=self.on_response,
                                   auto_ack=True)

    def on_response(self, ch, method, properties, body):
        notification = json.loads(body)
        print(f"New Notification: {notification['youtuber']} uploaded {notification['video_name']}")

    def send_user_request(self, youtuber_name=None, subscribe=None):
        request = {'user': self.username, 'login': True}
        if youtuber_name is not None and subscribe is not None:
            request.update({'youtuber': youtuber_name, 'subscribe': subscribe})
        self.channel.basic_publish(exchange='direct_logs', routing_key='user', body=json.dumps(request))
        print("SUCCESS: User request sent to the server")

    def start_receiving_notifications(self):
        print(f"[*] {self.username} is waiting for notifications. To exit press CTRL+C")
        self.channel.start_consuming()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: User.py <Username> [<Subscribe/Unsubscribe> <YoutuberName>]")
        sys.exit(1)

    username = sys.argv[1]
    user = User(username)

    if len(sys.argv) == 4:
        action = sys.argv[2].lower()
        youtuber_name = sys.argv[3]
        subscribe = True if action == 's' else False
        user.send_user_request(youtuber_name, subscribe)

    user.start_receiving_notifications()
