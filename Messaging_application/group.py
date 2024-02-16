import zmq
import threading
import json
import sys
from datetime import datetime

class GroupServer:
    def __init__(self, group_name, message_server_endpoint, group_ip, group_port):
        self.group_name = group_name
        self.message_server_endpoint = message_server_endpoint
        self.group_ip = group_ip  # External IP for registration
        self.group_port = int(group_port)
        self.context = zmq.Context()
        self.frontend_socket = self.context.socket(zmq.REP)
        # Bind to all interfaces for accepting local and external connections
        self.frontend_socket.bind(f"tcp://*:{self.group_port}")
        self.users = set()
        self.messages = []

    def register_with_message_server(self):
        """Registers the group with the central message server using the external IP."""
        try:
            with self.context.socket(zmq.REQ) as server_socket:
                server_socket.connect(self.message_server_endpoint)
                # Use the external IP for registration
                server_socket.send_json({
                    'action': 'register',
                    'group_name': self.group_name,
                    'group_address': f"tcp://{self.group_ip}:{self.group_port}"
                })
                response = server_socket.recv_json()
                print(f"Registration response: {response.get('response')}")
        except zmq.ZMQError as e:
            print(f"Failed to register with message server: {e}")

    def handle_join(self, user_uuid):
        """Handles a user's request to join the group."""
        if user_uuid not in self.users:
            self.users.add(user_uuid)
            print(f"JOIN REQUEST FROM {user_uuid}")
            return 'SUCCESS'
        return 'ALREADY_JOINED'

    def handle_leave(self, user_uuid):
        """Handles a user's request to leave the group."""
        if user_uuid in self.users:
            self.users.remove(user_uuid)
            print(f"LEAVE REQUEST FROM {user_uuid}")
            return 'SUCCESS'
        return 'NOT_A_MEMBER'

    def handle_send_message(self, user_uuid, message):
        """Stores the message sent by a user."""
        if user_uuid in self.users:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.messages.append((timestamp, user_uuid, message))
            print(f"MESSAGE FROM {user_uuid}: {message}")
            return 'SUCCESS'
        return 'USER_NOT_FOUND'

    def handle_get_messages(self, user_uuid, timestamp=None):
        """Sends all messages to the user, filtered by timestamp if provided."""
        if user_uuid not in self.users:
            return {'response': 'USER_NOT_FOUND'}
        
        filtered_messages = self.messages
        if timestamp:
            try:
                timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                filtered_messages = [msg for msg in self.messages if datetime.strptime(msg[0], '%Y-%m-%d %H:%M:%S') >= timestamp]
            except ValueError:
                return {'response': 'INVALID_TIMESTAMP'}

        print(f"MESSAGES REQUEST FROM {user_uuid}")
        return {'response': 'SUCCESS', 'messages': filtered_messages}

    def process_requests(self):
        """Processes incoming requests from users."""
        while True:
            try:
                message = self.frontend_socket.recv_json()
                action = message.get('action')
                user_uuid = message.get('user_uuid')
                response = {}

                if action == 'join':
                    response['response'] = self.handle_join(user_uuid)
                elif action == 'leave':
                    response['response'] = self.handle_leave(user_uuid)
                elif action == 'send_message':
                    message_text = message.get('message')
                    response['response'] = self.handle_send_message(user_uuid, message_text)
                elif action == 'get_messages':
                    timestamp = message.get('timestamp', None)
                    response = self.handle_get_messages(user_uuid, timestamp)
                else:
                    response['response'] = 'INVALID_ACTION'

                self.frontend_socket.send_json(response)
            except Exception as e:
                print(f"An error occurred: {e}")
                # Send a failure response to avoid hanging the client
                self.frontend_socket.send_json({'response': 'FAIL', 'reason': str(e)})

    def start(self):
        """Starts the server and begins processing requests."""
        self.register_with_message_server()
        request_thread = threading.Thread(target=self.process_requests)
        request_thread.start()
        request_thread.join()

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python group.py <group_name> <message_server_endpoint> <group_ip> <group_port>")
        sys.exit(1)

    # Adjust to receive the group's IP address as an argument
    group_server = GroupServer(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    print(f"Group '{sys.argv[1]}' listening at tcp://{sys.argv[3]}:{sys.argv[4]}")
    group_server.start()
