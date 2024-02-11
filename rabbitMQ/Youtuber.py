import pika
import sys
import json

class Youtuber:
    def __init__(self, youtuber_name):
        self.youtuber_name = youtuber_name
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        
        # Declare the exchange if it doesn't exist
        self.channel.exchange_declare(exchange='direct_logs', exchange_type='direct')
        
        # Declare the queue if it doesn't exist
        self.channel.queue_declare(queue='video_uploads')
        
        # Bind the queue to the exchange with the routing key
        self.channel.queue_bind(exchange='direct_logs', queue='video_uploads', routing_key='video')

    def publish_video(self, video_name):
        # Create the message as a JSON object
        message = json.dumps({
            'youtuber': self.youtuber_name,
            'video_name': video_name
        })
        
        # Publish the message to the exchange with the appropriate routing key
        self.channel.basic_publish(
            exchange='direct_logs',
            routing_key='video',
            body=message
        )
        
        print(f"SUCCESS: {self.youtuber_name} published a video titled '{video_name}'.")

    def close_connection(self):
        self.connection.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: Youtuber.py <YoutuberName> <VideoName>")
        sys.exit(1)

    youtuber_name = sys.argv[1]
    video_name = ' '.join(sys.argv[2:])
    youtuber = Youtuber(youtuber_name)
    youtuber.publish_video(video_name)
    youtuber.close_connection()
