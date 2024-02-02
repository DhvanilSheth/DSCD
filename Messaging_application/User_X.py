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
            print(f"New message received: {message}")
        except zmq.Again:
            continue  # No message received

def join_group(group_address):
    group_socket = context.socket(zmq.DEALER)
    group_socket.setsockopt(zmq.IDENTITY, USER_ID)
    group_socket.connect(group_address)

    listener_thread = threading.Thread(target=message_listener, args=(group_socket,))
    listener_thread.daemon = True
    listener_thread.start()

    join_request = {'operation': 'joinGroup', 'user_id': USER_ID.decode()}
    group_socket.send_json(join_request)
    response = group_socket.recv_string()
    print("Join group response:", response)

    return group_socket

def leave_group(group_socket):
    leave_request = {'operation': 'leaveGroup', 'user_id': USER_ID.decode()}
    group_socket.send_json(leave_request)
    response = group_socket.recv_string()
    print("Leave group response:", response)
    group_socket.close()

def send_message(group_socket, message):
    send_request = {'operation': 'sendMessage', 'text': message, 'user_id': USER_ID.decode()}
    group_socket.send_json(send_request)
    response = group_socket.recv_string()
    print("Send message response:", response)

def get_messages(group_socket, timestamp=None):
    get_request = {'operation': 'getMessage', 'timestamp': timestamp, 'user_id': USER_ID.decode()}
    group_socket.send_json(get_request)
    messages = group_socket.recv_string()
    print("Messages received:", messages)

def user_interface():
    group_socket = None
    while True:
        print("\nMenu:")
        print("1. Get list of groups")
        print("2. Join a group")
        print("3. Send a message")
        print("4. Get messages")
        print("5. Leave group")
        print("6. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            groups = get_group_list()
            print("Available groups:", json.dumps(groups, indent=2))
        elif choice == "2":
            if not group_socket:
                group_address = input("Enter group address to join (e.g., tcp://localhost:5557): ")
                group_socket = join_group(group_address)
            else:
                print("Already in a group. Please leave the current group before joining another.")
        elif choice == "3":
            if group_socket:
                message = input("Enter message to send: ")
                send_message(group_socket, message)
            else:
                print("Please join a group first.")
        elif choice == "4":
            if group_socket:
                timestamp = input("Enter timestamp to get messages since (or press enter for all messages): ")
                get_messages(group_socket, timestamp)
            else:
                print("Please join a group first.")
        elif choice == "5":
            if group_socket:
                leave_group(group_socket)
                group_socket = None
            else:
                print("Not currently in any group.")
        elif choice == "6":
            if group_socket:
                leave_group(group_socket)
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        user_interface()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        group_list_socket.close()
        context.term()
