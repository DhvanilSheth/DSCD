import zmq
import json
import threading
import uuid
from datetime import datetime

# Constants
MESSAGE_SERVER_IP = "localhost"
GROUP_LIST_PORT = "5556"
USER_ID = str(uuid.uuid4())

# ZeroMQ Context
context = zmq.Context()

# Socket to get the list of groups from the message server
group_list_socket = context.socket(zmq.REQ)
group_list_socket.connect(f"tcp://{MESSAGE_SERVER_IP}:{GROUP_LIST_PORT}")

# Function to get the list of groups from the server
def get_group_list():
    group_list_socket.send_string("GET_GROUP_LIST")
    groups = group_list_socket.recv_string()
    return json.loads(groups)

# Function to process incoming messages from a group
def message_listener(group_socket):
    while True:
        message = group_socket.recv_string()
        print(f"New message received: {message}")

# Function to join a group
def join_group(group_address):
    group_socket = context.socket(zmq.DEALER)
    group_socket.setsockopt(zmq.IDENTITY, USER_ID.encode())
    group_socket.connect(group_address)

    # Start listening for messages in a separate thread
    threading.Thread(target=message_listener, args=(group_socket,)).start()

    # Send join request
    join_request = {'operation': 'joinGroup', 'user_id': USER_ID}
    group_socket.send_json(join_request)
    response = group_socket.recv_string()
    print(response)

    return group_socket

# Function to leave a group
def leave_group(group_socket):
    leave_request = {'operation': 'leaveGroup', 'user_id': USER_ID}
    group_socket.send_json(leave_request)
    response = group_socket.recv_string()
    print(response)
    group_socket.close()

# Function to send a message to a group
def send_message(group_socket, message):
    send_request = {'operation': 'sendMessage', 'text': message, 'user_id': USER_ID}
    group_socket.send_json(send_request)
    response = group_socket.recv_string()
    print(response)

# Function to get messages from a group
def get_messages(group_socket, timestamp=None):
    get_request = {'operation': 'getMessage', 'timestamp': timestamp, 'user_id': USER_ID}
    group_socket.send_json(get_request)
    messages = group_socket.recv_string()
    print(messages)

if __name__ == "__main__":
    try:
        # Get the list of groups from the server
        groups = get_group_list()
        print(f"Available groups: {groups}")

        if groups:
            # Just for example, join the first group
            group_info = list(groups[0].values())[0]
            group_socket = join_group(group_info['address'])

            # Example of sending a message
            send_message(group_socket, "Hello Group!")

            # Example of getting all messages
            get_messages(group_socket)

            # Example of getting messages after a specific timestamp
            timestamp = datetime.now().strftime('%H:%M:%S')
            get_messages(group_socket, timestamp)

            # Leave the group
            leave_group(group_socket)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        context.term()
