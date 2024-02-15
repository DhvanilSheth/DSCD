import pika
import threading
import json
import time

# Global storage for user data and notifications
users_data = {}  # Structure: {username: {'subscriptions': set(), 'notifications': []}}
youtubers_data = {}  # Structure: {youtuber_name: ['video1', 'video2', ...]}

def create_channel():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    return connection, channel

def notify_users(youtuber, video_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    for username, data in users_data.items():
        if youtuber in data['subscriptions']:
            notification = f"{youtuber} uploaded {video_name}"
            data['notifications'].append(notification)
            
            # Define user-specific notification queue
            personal_queue = f'notifications_{username}'
            channel.queue_declare(queue=personal_queue)

            # Publish the notification to the user's personal queue
            channel.basic_publish(
                exchange='',
                routing_key=personal_queue,
                body=json.dumps({'user': username, 'message': notification})
            )
            print(f"Notification sent to {username}: {notification}")

    connection.close()

def consume_user_requests():
    connection, channel = create_channel()

    channel.queue_declare(queue='user_requests')

    def callback(ch, method, properties, body):
        user_request = json.loads(body)
        username = user_request['user']

        # Initialize user data if new
        if username not in users_data:
            users_data[username] = {'subscriptions': set(), 'notifications': []}
            print(f"{username} joined the platform!")

        if 'youtuber' in user_request:
            youtuber_name = user_request['youtuber']
            if user_request['subscribe']:
                users_data[username]['subscriptions'].add(youtuber_name)
                action = 'subscribed'
            else:
                users_data[username]['subscriptions'].remove(youtuber_name)
                action = 'unsubscribed'
            print(f"{username} {action} to {youtuber_name}")
        else:
            # User logged in, print notifications if any
            print(f"{username} logged in")
            for notification in users_data[username]['notifications']:
                print(f"Notification for {username}: {notification}")
            # Clear notifications after showing them
            users_data[username]['notifications'] = []

    while True:
        method_frame, header_frame, body = channel.basic_get('user_requests')
        if method_frame:
            callback(channel, method_frame, header_frame, body)
            channel.basic_ack(method_frame.delivery_tag)
        else:
            time.sleep(1)  # Wait for 1 second before checking the queue again

def consume_youtuber_requests():
    connection, channel = create_channel()

    channel.queue_declare(queue='youtuber_uploads')

    def callback(ch, method, properties, body):
        upload_request = json.loads(body)
        youtuber_name = upload_request['youtuber']
        video_name = upload_request['video']

        # Initialize youtuber data if new
        if youtuber_name not in youtubers_data:
            youtubers_data[youtuber_name] = []
        youtubers_data[youtuber_name].append(video_name)

        print(f"{youtuber_name} uploaded {video_name}")
        notify_users(youtuber_name, video_name)

    while True:
        method_frame, header_frame, body = channel.basic_get('youtuber_uploads')
        if method_frame:
            callback(channel, method_frame, header_frame, body)
            channel.basic_ack(method_frame.delivery_tag)
        else:
            time.sleep(1)  # Wait for 1 second before checking the queue again

if __name__ == "__main__":
    user_thread = threading.Thread(target=consume_user_requests)
    user_thread.daemon = True
    user_thread.start()

    youtuber_thread = threading.Thread(target=consume_youtuber_requests)
    youtuber_thread.daemon = True
    youtuber_thread.start()

    user_thread.join()
    youtuber_thread.join()