import zmq
import json

class MessageServer:
    def __init__(self, port=5555):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://*:{port}")
        self.groups = {}  # Stores group info as {group_name: group_address}

    def run(self):
        print("Message Server started on port 5555...")
        while True:
            try:
                message = self.socket.recv_json()
                action = message.get('action')

                if action == 'register':
                    group_name = message.get('group_name')
                    group_address = message.get('group_address')
                    # Register the group if it's not already registered
                    if group_name not in self.groups:
                        self.groups[group_name] = group_address
                        print(f"JOIN REQUEST FROM {group_address} [IP: PORT]")
                        response = {'response': 'SUCCESS'}
                    else:
                        response = {'response': 'FAIL', 'reason': 'Group already registered'}
                elif action == 'list_groups':
                    user_uuid = message.get('user_uuid')  # Extract the UUID
                    print(f"GROUP LIST REQUEST FROM {user_uuid}")  # Log the requester's UUID
                    response = self.groups
                else:
                    response = {'response': 'INVALID REQUEST'}

                # Send back the appropriate response
                self.socket.send_json(response)
            except Exception as e:
                print(f"An error occurred: {e}")
                # Sending back a fail response in case of an error to avoid hanging the client
                self.socket.send_json({'response': 'FAIL', 'reason': str(e)})

if __name__ == "__main__":
    server = MessageServer()
    server.run()
