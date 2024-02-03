import zmq
import json
import threading
import argparse
import uuid

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

# Function to create and connect a REQ socket for group list requests
def get_group_list_socket():
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{MESSAGE_SERVER_IP}:{GROUP_LIST_PORT}")
    return socket

def message_listener(group_socket):
    while True:
        try:
            message = group_socket.recv_string()
            print("\nReceived:", message)
        except zmq.ZMQError:
            break  # Exit the loop if the socket is closed

def join_group(group_address):
    group_socket = context.socket(zmq.DEALER)
    group_socket.setsockopt(zmq.IDENTITY, USER_ID)
    group_socket.connect(group_address)
    
    listener_thread = threading.Thread(target=message_listener, args=(group_socket,))
    listener_thread.start()
    
    group_socket.send_json({'operation': 'joinGroup', 'user_id': USER_ID.decode()})
    return group_socket, listener_thread

def leave_group(group_socket):
    if group_socket:
        group_socket.send_json({'operation': 'leaveGroup', 'user_id': USER_ID.decode()})
        group_socket.close()
        print("Left the group successfully.")
    else:
        print("You are not currently in a group.")

def send_message(group_socket, message):
    if group_socket:
        group_socket.send_json({'operation': 'sendMessage', 'text': message, 'user_id': USER_ID.decode()})
    else:
        print("Please join a group first.")

def get_messages(group_socket):
    if group_socket:
        group_socket.send_json({'operation': 'getMessage', 'user_id': USER_ID.decode()})
    else:
        print("Please join a group first.")

def user_interface():
    group_socket = None
    while True:
        print("\n1. Get list of groups")
        print("2. Join a group")
        print("3. Send a message")
        print("4. Get messages")
        print("5. Leave group")
        print("6. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            socket = get_group_list_socket()
            socket.send_string("GET_GROUP_LIST")
            groups = socket.recv_string()
            print("Available groups:", groups)
            socket.close()
        elif choice == "2" and not group_socket:
            group_address = input("Enter group address (e.g., tcp://localhost:5557): ")
            group_socket, _ = join_group(group_address)
            print("Joined the group successfully.")
        elif choice == "3" and group_socket:
            message = input("Enter your message: ")
            send_message(group_socket, message)
        elif choice == "4" and group_socket:
            get_messages(group_socket)
        elif choice == "5" and group_socket:
            leave_group(group_socket)
            group_socket = None  # Reset the socket after leaving
        elif choice == "6":
            if group_socket:
                leave_group(group_socket)
            print("Exiting...")
            break
        else:
            print("Invalid option or action not allowed in the current state.")

if __name__ == "__main__":
    user_interface()
