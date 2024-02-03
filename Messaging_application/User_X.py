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

# Function to create and connect a REQ socket
def connect_req_socket(ip, port):
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{ip}:{port}")
    return socket

# Function to get the list of groups from the server
def get_group_list():
    socket = connect_req_socket(MESSAGE_SERVER_IP, GROUP_LIST_PORT)
    socket.send_string("GET_GROUP_LIST")
    response = socket.recv_string()
    socket.close()
    return json.loads(response)

def message_listener(group_socket):
    while True:
        try:
            message = group_socket.recv_string(zmq.NOBLOCK)  # Non-blocking receive
            print(f"\nNew message received: {message}")
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

    return group_socket, listener_thread

def leave_group(group_socket):
    if group_socket:
        leave_request = {'operation': 'leaveGroup', 'user_id': USER_ID.decode()}
        group_socket.send_json(leave_request)
        response = group_socket.recv_string()
        print("Leave group response:", response)
        group_socket.close()
        return None
    else:
        print("You are not in a group.")
        return None

def send_message(group_socket, message):
    if group_socket:
        send_request = {'operation': 'sendMessage', 'text': message, 'user_id': USER_ID.decode()}
        group_socket.send_json(send_request)
        response = group_socket.recv_string()
        print("Send message response:", response)
    else:
        print("You need to join a group first.")

def get_messages(group_socket, timestamp=None):
    if group_socket:
        get_request = {'operation': 'getMessage', 'timestamp': timestamp, 'user_id': USER_ID.decode()}
        group_socket.send_json(get_request)
        messages = group_socket.recv_string()
        print("Messages received:", messages)
    else:
        print("You need to join a group first.")

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
            if group_socket:
                print("Already in a group. Please leave the current group before joining another.")
            else:
                group_address = input("Enter group address to join (e.g., tcp://localhost:5557): ")
                group_socket, _ = join_group(group_address)
        elif choice == "3":
            message = input("Enter message to send: ")
            send_message(group_socket, message)
        elif choice == "4":
            timestamp = input("Enter timestamp to get messages since (or press enter for all messages): ")
            get_messages(group_socket, timestamp)
        elif choice == "5":
            group_socket = leave_group(group_socket)
        elif choice == "6":
            if group_socket:
                leave_group(group_socket)
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        user_interface()
    except KeyboardInterrupt:
        print("\nUser client exiting gracefully.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        context.term()
