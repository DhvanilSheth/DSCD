import zmq
import json

class MessageServer:
    def __init__(self, port=5555):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{port}")
        self.groups = {}  # Dictionary to store group info, e.g., {group_name: group_address}

    def register_group(self, group_name, group_address):
        """Register a new group with the server."""
        if group_name not in self.groups:
            self.groups[group_name] = group_address
            print(f"JOIN REQUEST FROM {group_address} [IP: PORT]")
            return "SUCCESS"
        return "FAIL"

    def list_groups(self):
        """Provide a list of registered groups."""
        return json.dumps(self.groups)

    def run(self):
        """Run the message server."""
        try:
            while True:
                # Wait for the next request from a client
                message = self.socket.recv_json()
                if message['action'] == 'register':
                    response = self.register_group(message['group_name'], message['group_address'])
                elif message['action'] == 'list_groups':
                    response = self.list_groups()
                else:
                    response = "INVALID REQUEST"

                # Send the reply back to the client
                self.socket.send_json({"response": response})
        except KeyboardInterrupt:
            print("Message server is shutting down...")
        finally:
            self.socket.close()
            self.context.term()

if __name__ == "__main__":
    server = MessageServer()
    print("Message Server started...")
    server.run()
