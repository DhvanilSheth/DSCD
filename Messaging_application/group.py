import zmq
import threading
import json
import sys
from datetime import datetime

class GroupServer:
    def __init__(self, group_name, message_server_endpoint, group_port):
        self.group_name = group_name
        self.message_server_endpoint = message_server_endpoint
        self.group_port = group_port  # Add this line to save the group_port as an instance attribute
        self.context = zmq.Context()
        self.group_socket = self.context.socket(zmq.REP)
        self.group_socket.bind(f"tcp://*:{group_port}")
        self.users = {}
        self.messages = []

    def register_with_message_server(self):
        """Register the group with the central message server."""
        message_server_socket = self.context.socket(zmq.REQ)
        message_server_socket.connect(self.message_server_endpoint)
        # Use self.group_port which is now correctly defined
        full_address = f"tcp://localhost:{self.group_port}"
        message_server_socket.send_json({
            'action': 'register',
            'group_name': self.group_name,
            'group_address': full_address
        })
        response = message_server_socket.recv_json()
        message_server_socket.close()
        return response
    
    def handle_join_request(self, user_uuid):
        """Handle a join request from a user."""
        if user_uuid not in self.users:
            self.users[user_uuid] = None  # Placeholder for user socket
            return "SUCCESS"
        return "FAIL"

    def handle_leave_request(self, user_uuid):
        """Handle a leave request from a user."""
        if user_uuid in self.users:
            del self.users[user_uuid]
            print(f"LEAVE REQUEST FROM {user_uuid} [UUID OF USER]")
            return "SUCCESS"
        return "FAIL"

    def handle_send_message(self, user_uuid, message):
        """Handle sending a message from a user."""
        if user_uuid in self.users:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.messages.append((timestamp, user_uuid, message))
            print(f"MESSAGE FROM {user_uuid}: {message}")
            return "SUCCESS"
        return "FAIL"

    def handle_get_message(self, user_uuid, timestamp=None):
        """Handle a request to get messages."""
        if user_uuid not in self.users:
            return "FAIL"
        filtered_messages = [msg for msg in self.messages if timestamp is None or msg[0] >= timestamp]
        print(f"MESSAGES REQUESTED BY {user_uuid}")
        return json.dumps(filtered_messages)

    def serve_user_requests(self):
        """Serve incoming requests from users."""
        while True:
            message = self.group_socket.recv_json()
            action = message['action']
            user_uuid = message['user_uuid']
            response = ""

            if action == 'join':
                response = self.handle_join_request(user_uuid)
                print(f"JOIN REQUEST FROM {user_uuid} [UUID OF USER]")
            elif action == 'leave':
                response = self.handle_leave_request(user_uuid)
            elif action == 'send_message':
                response = self.handle_send_message(user_uuid, message['message'])
            elif action == 'get_message':
                response = self.handle_get_message(user_uuid, message.get('timestamp'))
            else:
                response = "INVALID REQUEST"

            self.group_socket.send_json({"response": response})

    def run(self):
        """Run the group server."""
        register_response = self.register_with_message_server()
        print(f"Registration with message server: {register_response['response']}")

        user_request_thread = threading.Thread(target=self.serve_user_requests)
        user_request_thread.start()
        user_request_thread.join()

        self.group_socket.close()
        self.context.term()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python group_server.py <group_name> <message_server_endpoint> <group_port>")
        sys.exit(1)

    group_name = sys.argv[1]
    message_server_endpoint = sys.argv[2]
    group_port = sys.argv[3]

    server = GroupServer(group_name, message_server_endpoint, group_port)
    print(f"Group Server '{group_name}' started on port {group_port}...")
    server.run()
