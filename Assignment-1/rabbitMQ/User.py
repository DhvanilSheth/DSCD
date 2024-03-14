import pika
import sys
import json

def send_user_request(username, youtuber=None, subscribe=None):
    credentials = pika.PlainCredentials('instance-2', 'vhavle')
    parameters = pika.ConnectionParameters('10.128.0.2', 5672, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue='user_requests')

    user_request = {'user': username}
    if youtuber:
        user_request['youtuber'] = youtuber
        user_request['subscribe'] = subscribe

    channel.basic_publish(exchange='', routing_key='user_requests', body=json.dumps(user_request))
    print("SUCCESS")

    connection.close()

def receive_notifications(username):
    credentials = pika.PlainCredentials('instance-2', 'vhavle')
    parameters = pika.ConnectionParameters('10.128.0.2', 5672, '/', credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Declare a personal queue for the user to receive direct messages
    personal_queue = f'notifications_{username}'
    channel.queue_declare(queue=personal_queue)

    def callback(ch, method, properties, body):
        notification = json.loads(body)
        print(f"New Notification: {notification['message']}")

    channel.basic_consume(queue=personal_queue, on_message_callback=callback, auto_ack=True)
    
    print(f"[*] Waiting for notifications for {username}. To exit press CTRL+C")
    try:
        channel.start_consuming()
    finally:
        connection.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python User.py <username> [s|u <YoutuberName>]")
        sys.exit(1)

    username = sys.argv[1]
    youtuber = sys.argv[3] if len(sys.argv) > 3 else None
    subscribe = sys.argv[2] == 's' if len(sys.argv) > 3 else None

    send_user_request(username, youtuber, subscribe)
    receive_notifications(username)
