import zmq
import json
import threading
import uuid
from datetime import datetime

# Constants
MESSAGE_SERVER_IP = "localhost"
MESSAGE_SERVER_REGISTRATION_PORT = "5555"
GROUP_PORT = "5557"
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"

# ZeroMQ Context
context = zmq.Context()

# Socket to register with message server
registration_socket = context.socket(zmq.REQ)
registration_socket.connect(f"tcp://{MESSAGE_SERVER_IP}:{MESSAGE_SERVER_REGISTRATION_PORT}")

# Socket to communicate with users
user_communication_socket = context.socket(zmq.ROUTER)
user_communication_socket.bind(f"tcp://*:{GROUP_PORT}")

# Group information
group_id = str(uuid.uuid4())
group_name = "Group1"
group_address = f"tcp://localhost:{GROUP_PORT}"

# Data structure to maintain user list and messages
user_tele = {}  # {user_id: user_socket}
messages = []  # [(timestamp, message)]

def register_with_message_server():
    registration_socket.send_json({
        'id': group_id,
        'name': group_name,
        'address': group_address
    })
    response = registration_socket.recv_string()
    if response == SUCCESS:
        print(f"Server registered successfully with ID {group_id}")
    else:
        print(f"Server registration failed with ID {group_id}")

def handle_user_requests():
    while True:
        # Use a new thread for each user request
        user_id, message = user_communication_socket.recv_multipart()
        threading.Thread(target=process_user_request, args=(user_id, message)).start()

def process_user_request(user_id, message):
    message = json.loads(message.decode())
    operation = message['operation']

    if operation == 'joinGroup':
        user_tele[user_id] = group_id
        print(f"JOIN REQUEST FROM {user_id.decode()}")
        user_communication_socket.send_multipart([user_id, SUCCESS.encode()])

    elif operation == 'leaveGroup':
        user_tele.pop(user_id, None)
        print(f"LEAVE REQUEST FROM {user_id.decode()}")
        user_communication_socket.send_multipart([user_id, SUCCESS.encode()])

    elif operation == 'getMessage':
        timestamp = message.get('timestamp')
        messages_to_send = get_messages_since(timestamp)
        response = json.dumps(messages_to_send)
        user_communication_socket.send_multipart([user_id, response.encode()])

    elif operation == 'sendMessage':
        if user_id in user_tele:
            text = message['text']
            timestamp = datetime.now().strftime('%H:%M:%S')
            messages.append((timestamp, text))
            print(f"MESSAGE RECEIVED FROM {user_id.decode()}: {text}")
            user_communication_socket.send_multipart([user_id, SUCCESS.encode()])
        else:
            user_communication_socket.send_multipart([user_id, FAILURE.encode()])

def get_messages_since(timestamp):
    if timestamp:
        return [msg for msg in messages if msg[0] >= timestamp]
    else:
        return messages

if __name__ == "__main__":
    register_with_message_server()
    threading.Thread(target=handle_user_requests).start()
