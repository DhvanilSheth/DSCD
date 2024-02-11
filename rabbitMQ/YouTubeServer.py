import pika
import json

class YouTubeServer:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        # Declare the exchange and queues
        self.channel.exchange_declare(exchange='direct_logs', exchange_type='direct')

        # User requests queue
        self.channel.queue_declare(queue='user_requests')
        self.channel.queue_bind(exchange='direct_logs', queue='user_requests', routing_key='user')

        # YouTuber requests queue
        self.channel.queue_declare(queue='youtuber_requests')
        self.channel.queue_bind(exchange='direct_logs', queue='youtuber_requests', routing_key='youtuber')

        self.users = {}
        self.videos = {}

    def consume_user_requests(self):
        def callback(ch, method, properties, body):
            user_request = json.loads(body)
            username = user_request['user']
            if user_request['action'] == 'login':
                print(f"{username} logged in")
                # Send the notifications for the videos uploaded while user was logged out
                for youtuber in self.users.get(username, {}).get('subscriptions', []):
                    for video in self.videos.get(youtuber, []):
                        self.notify_users(username, youtuber, video)
            elif user_request['action'] in ['subscribe', 'unsubscribe']:
                action = 'subscribed' if user_request['action'] == 'subscribe' else 'unsubscribed'
                youtuber = user_request['youtuber']
                self.update_subscription(username, youtuber, user_request['action'] == 'subscribe')
                print(f"{username} {action} to {youtuber}")

        self.channel.basic_consume(queue='user_requests', on_message_callback=callback, auto_ack=True)
        print('YouTubeServer is now consuming user requests...')
        self.channel.start_consuming()

    def consume_youtuber_requests(self):
        def callback(ch, method, properties, body):
            youtuber_request = json.loads(body)
            youtuber_name = youtuber_request['youtuber']
            video_name = youtuber_request['video']
            self.add_video(youtuber_name, video_name)
            print(f"{youtuber_name} uploaded {video_name}")
            # Notify all subscribers of this youtuber
            for user in self.users:
                if youtuber_name in self.users[user].get('subscriptions', []):
                    self.notify_users(user, youtuber_name, video_name)

        self.channel.basic_consume(queue='youtuber_requests', on_message_callback=callback, auto_ack=True)
        print('YouTubeServer is now consuming youtuber requests...')
        self.channel.start_consuming()

    def update_subscription(self, username, youtuber, subscribe):
        if username not in self.users:
            self.users[username] = {'subscriptions': []}
        if subscribe:
            self.users[username]['subscriptions'].append(youtuber)
        else:
            self.users[username]['subscriptions'].remove(youtuber)

    def add_video(self, youtuber_name, video_name):
        if youtuber_name not in self.videos:
            self.videos[youtuber_name] = []
        self.videos[youtuber_name].append(video_name)

    def notify_users(self, username, youtuber_name, video_name):
        print(f"Notification: {username}, {youtuber_name} uploaded {video_name}")

    def start_server(self):
        self.consume_user_requests()
        self.consume_youtuber_requests()

if __name__ == '__main__':
    server = YouTubeServer()
    server.start_server()
