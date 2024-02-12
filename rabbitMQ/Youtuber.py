import pika
import sys
import json

def publish_video(youtuber, video_name):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    
    channel.queue_declare(queue='youtuber_uploads')

    message = json.dumps({'youtuber': youtuber, 'video': video_name})
    channel.basic_publish(exchange='', routing_key='youtuber_uploads', body=message)
    print("SUCCESS")
    
    connection.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python Youtuber.py <YoutuberName> <VideoName>")
        sys.exit(1)
    
    youtuber_name = sys.argv[1]
    video_name = ' '.join(sys.argv[2:])
    publish_video(youtuber_name, video_name)
