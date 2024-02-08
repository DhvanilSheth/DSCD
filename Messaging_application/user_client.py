import zmq
import sys
import json
from datetime import datetime
import uuid

class UserClient:
    def __init__(self, message_server_endpoint):
        self.user_uuid = str(uuid.uuid4())
        self.message_server_endpoint = message_server_endpoint
        self.context = zmq.Context()
        self.server_socket = self.context.socket(zmq.REQ)
        self.server_socket.connect(message_server_endpoint)
        self.group_sockets = {}  # Dictionary to store group sockets
        self.groups = {} 


    def get_group_list(self):
        """Request the list of available groups from the message server."""
        self.server_socket.send_json({'action': 'list_groups'})
        response = self.server_socket.recv_json()
        return json.loads(response['response'])

    def refresh_group_list(self):
        """Refresh the cached list of groups from the message server."""
        self.groups = self.get_group_list()

    def join_group_by_address(self, group_address):
        """Join a group using the group's address, if it is registered."""
        # Refresh the list of groups from the message server
        self.refresh_group_list()

        # Normalize the address to ensure the protocol is included
        if not group_address.startswith("tcp://"):
            group_address = f"tcp://{group_address}"

        # Check if the provided address is in the list of registered groups
        if group_address not in self.groups.values():
            print(f"The group with address {group_address} is not registered with the server.")
            return

        # Proceed with joining the group
        group_socket = self.context.socket(zmq.REQ)
        group_socket.connect(group_address)
        group_socket.send_json({'action': 'join', 'user_uuid': self.user_uuid})
        response = group_socket.recv_json()
        if response['response'] == "SUCCESS":
            # The address is being used as a unique identifier for the group
            self.group_sockets[group_address] = group_socket
            print(f"Joining {group_address}: {response['response']}")
        else:
            print(f"Failed to join {group_address}: {response['response']}")

    def leave_group(self, group_address):
    """Leave a specified group."""
    if group_address in self.group_sockets:
        group_socket = self.group_sockets[group_address]
        group_socket.send_json({'action': 'leave', 'user_uuid': self.user_uuid})
        response = group_socket.recv_json()
        group_socket.close()
        del self.group_sockets[group_address]
        print(f"Leaving group {group_address}: {response['response']}")
    else:
        print("Not a member of the specified group.")

    def send_message(self, group_address, message):
        """Send a message to a specified group."""
        if group_address in self.group_sockets:
            group_socket = self.group_sockets[group_address]
            group_socket.send_json({'action': 'send_message', 'user_uuid': self.user_uuid, 'message': message})
            response = group_socket.recv_json()
            print(f"Sending message to {group_address}: {response['response']}")
        else:
            print("Not a member of the specified group.")

    def get_messages(self, group_address, timestamp=None):
        """Get messages from a specified group."""
        if group_address in self.group_sockets:
            group_socket = self.group_sockets[group_address]
            request = {'action': 'get_message', 'user_uuid': self.user_uuid}
            if timestamp:
                request['timestamp'] = timestamp
            group_socket.send_json(request)
            response = group_socket.recv_json()
            messages = json.loads(response['response'])
            for msg in messages:
                print(f"{msg[0]} - {msg[1]}: {msg[2]}")
        else:
            print("Not a member of the specified group.")

    def run(self):
        """Run the user client interface."""
        print(f"Your User UUID is: {self.user_uuid}")
        while True:
            print("\nMenu:")
            print("1: Get list of groups")
            print("2: Join group")
            print("3: Leave group")
            print("4: Send message")
            print("5: Get messages")
            print("0: Exit")
            choice = input("Enter option: ")

            if choice == "1":
                self.groups = self.get_group_list()
                print("Available groups:")
                for group_name, group_address in self.groups.items():
                    print(f"{group_name} - {group_address}")
            elif choice == "2":
                # Before allowing to join, ensure we have the latest list of groups
                self.refresh_group_list()
                group_address = input("Enter the full address of the group to join (e.g., tcp://localhost:5556): ")
                self.join_group_by_address(group_address)
            elif choice == "3":
                group_name = input("Enter group name to leave: ")
                self.leave_group(group_name)
            elif choice == "4":
                group_name = input("Enter group name to send message: ")
                if group_name in self.groups:
                    message = input("Enter message: ")
                    self.send_message(group_name, message)
                else:
                    print("You are not a member of this group or it does not exist.")
            elif choice == "5":
                group_name = input("Enter group name to get messages: ")
                if group_name in self.groups:
                    timestamp = input("Enter timestamp (HH:MM:SS) or leave blank for all messages: ")
                    self.get_messages(group_name, timestamp)
                else:
                    print("You are not a member of this group or it does not exist.")
            elif choice == "0":
                print("Exiting...")
                for socket in self.group_sockets.values():
                    socket.close()
                self.server_socket.close()
                self.context.term()
                break
            else:
                print("Invalid option, please try again.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python user_client.py <message_server_endpoint>")
        sys.exit(1)

    message_server_endpoint = sys.argv[1]

    client = UserClient(message_server_endpoint)
    client.run()