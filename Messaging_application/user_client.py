import zmq
import sys
import uuid
import json
from datetime import datetime
import re

class UserClient:
    def __init__(self, message_server_endpoint):
        self.user_uuid = str(uuid.uuid4())
        self.message_server_endpoint = message_server_endpoint
        self.context = zmq.Context()
        self.server_socket = self.context.socket(zmq.REQ)
        self.server_socket.connect(message_server_endpoint)
        self.group_sockets = {}  # {group_address: zmq_socket}

    def get_group_list(self):
        """Fetches the list of available groups from the message server."""
        self.server_socket.send_json({'action': 'list_groups', 'user_uuid': self.user_uuid})
        response = self.server_socket.recv_json()
        if response:
            print("Available groups:")
            for group_name, group_address in response.items():
                print(f"{group_name} - {group_address}")
        else:
            print("No groups available or message server is down.")

    def join_group(self, group_address):
        """Joins a group specified by its address."""
        if group_address not in self.group_sockets:
            group_socket = self.context.socket(zmq.REQ)
            group_socket.connect(group_address)
            group_socket.send_json({'action': 'join', 'user_uuid': self.user_uuid})
            response = group_socket.recv_json()
            if response['response'] == 'SUCCESS':
                self.group_sockets[group_address] = group_socket
                print("Joined group successfully.")
            else:
                print("Failed to join group.")
        else:
            print("Already joined the group.")

    def leave_group(self, group_address):
        """Leaves a group specified by its address."""
        if group_address in self.group_sockets:
            group_socket = self.group_sockets[group_address]
            group_socket.send_json({'action': 'leave', 'user_uuid': self.user_uuid})
            response = group_socket.recv_json()
            if response['response'] == 'SUCCESS':
                group_socket.close()
                del self.group_sockets[group_address]
                print("Left group successfully.")
            else:
                print("Failed to leave group.")
        else:
            print("Not a member of this group.")

    def send_message(self, group_address, message):
        """Sends a message to the specified group."""
        if group_address in self.group_sockets:
            group_socket = self.group_sockets[group_address]
            group_socket.send_json({'action': 'send_message', 'user_uuid': self.user_uuid, 'message': message})
            response = group_socket.recv_json()
            print(f"Message send status: {response['response']}")
        else:
            print("Must join the group before sending messages.")

    def get_messages(self, group_address):
        """Fetches messages from the specified group."""
        if group_address in self.group_sockets:
            timestamp = input("Enter timestamp (YYYY-MM-DD HH:MM:SS) for filtered messages or press Enter for all: ").strip()
            # Validate timestamp format or use None for all messages
            formatted_timestamp = timestamp if re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', timestamp) else None

            group_socket = self.group_sockets[group_address]
            group_socket.send_json({'action': 'get_messages', 'user_uuid': self.user_uuid, 'timestamp': formatted_timestamp})
            response = group_socket.recv_json()
            if response['response'] == 'SUCCESS':
                print("Messages from group:")
                for msg in response['messages']:
                    print(f"{msg[0]} - {msg[1]}: {msg[2]}")
            else:
                print("Failed to get messages.")
        else:
            print("Must join the group to fetch messages.")

    def run(self):
        """Runs the user client, providing an interactive menu."""
        print(f"Your User UUID is: {self.user_uuid}")
        while True:
            print("\nOptions:")
            print("1: List available groups")
            print("2: Join group")
            print("3: Leave group")
            print("4: Send message")
            print("5: Get messages")
            print("0: Exit")
            choice = input("Enter option: ")

            if choice == "1":
                self.get_group_list()
            elif choice == "2":
                group_address = input("Enter the full address of the group to join (e.g., tcp://localhost:5556): ")
                self.join_group(group_address)
            elif choice == "3":
                group_address = input("Enter the full address of the group to leave: ")
                self.leave_group(group_address)
            elif choice == "4":
                group_address = input("Enter the full address of the group to send a message to: ")
                message = input("Enter your message: ")
                self.send_message(group_address, message)
            elif choice == "5":
                group_address = input("Enter the full address of the group to get messages from: ")
                self.get_messages(group_address)
            elif choice == "0":
                print("Exiting...")
                for socket in self.group_sockets.values():
                    socket.close()
                self.server_socket.close()
                self.context.term()
                break
            else:
                print("Invalid option. Please try again.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python user_client.py <message_server_endpoint>")
        sys.exit(1)

    message_server_endpoint = sys.argv[1]
    client = UserClient(message_server_endpoint)
    client.run()
