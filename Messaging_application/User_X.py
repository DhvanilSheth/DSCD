import zmq
import json
import threading
import argparse
import uuid
from datetime import datetime

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Start a user client.')
parser.add_argument('--user_id', type=str, default=str(uuid.uuid4()), help='User ID (optional, will be generated if not provided)')
parser.add_argument('--server_ip', type=str, default="localhost", help='IP address of the message server')
parser.add_argument('--server_port', type=str, default="5556", help='Port of the message server group list service')
args = parser.parse_args()

# Assign command-line arguments to variables
MESSAGE_SERVER_IP = args.server_ip
GROUP_LIST_PORT = args.server_port
USER_ID = args.user_id.encode()  # Encoding the UUID to bytes for ZeroMQ IDENTITY

# ZeroMQ Context
context = zmq.Context()

# Socket to get the list of groups from the message server
group_list_socket = context.socket(zmq.REQ)
group_list_socket.connect(f"tcp://{MESSAGE_SERVER_IP}:{GROUP_LIST_PORT}")

def get_group_list():
    group_list_socket.send_string("GET_GROUP_LIST")
    groups = group_list_socket.recv_string()
    return json.loads(groups)

def message_listener(group_socket):
    while True:
        try:
            message = group_socket.recv_string(zmq.NOBLOCK)  # Non-blocking receive
            if message:
                print(f"New message received: {message}")
        except zmq.Again:
            pass  # No message received, can include a sleep time if desired

def join_group(group_address):
    group_socket = context.socket(zmq.DEALER)
    group_socket.setsockopt(zmq.IDENTITY, USER_ID)
    group_socket.connect(group_address)

    listener_thread = threading.Thread(target=message_listener, args=(group_socket,))
    listener_thread.daemon = True  # Daemonize thread
    listener_thread.start()

    join_request = {'operation': 'joinGroup', 'user_id': USER_ID.decode()}
    group_socket.send_json(join_request)
    response = group_socket.recv_string()
    print(response)

    return group_socket

def leave_group(group_socket):
    leave_request = {'operation': 'leaveGroup', 'user_id': USER_ID.decode()}
    group_socket.send_json(leave_request)
    response = group_socket.recv_string()
    print(response)
    group_socket.close()

def send_message(group_socket, message):
    send_request = {'operation': 'sendMessage', 'text': message, 'user_id': USER_ID.decode()}
    group_socket.send_json(send_request)
    response = group_socket.recv_string()
    print(response)

def get_messages(group_socket, timestamp=None):
    get_request = {'operation': 'getMessage', 'timestamp': timestamp, 'user_id': USER_ID.decode()}
    group_socket.send_json(get_request)
    messages = group_socket.recv_string()
    print(messages)

if __name__ == "__main__":
    try:
        groups = get_group_list()
        print(f"Available groups: {groups}")

        # Example usage
        # Join the first available group
        if groups:
            group_info = list(groups[0].values())[0]
            group_socket = join_group(group_info['address'])

            # Send a message to the group
            send_message(group_socket, "Hello Group!")

            # Get all messages from the group
            get_messages(group_socket)

            # Assuming some time passes and more messages are sent...
            # Get messages after a specific timestamp
            later_timestamp = datetime.now().strftime('%H:%M:%S')
            get_messages(group_socket, later_timestamp)

            # Leave the group
            leave_group(group_socket)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        group_list_socket.close()
        context.term()
