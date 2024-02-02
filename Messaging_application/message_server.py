import zmq
import json
from collections import defaultdict

# Constants
REGISTRATION_PORT = "5555"
GROUP_LIST_PORT = "5556"
SUCCESS = "SUCCESS"
FAILURE = "FAILURE"

# ZeroMQ Context
context = zmq.Context()

# Socket to handle group server registration
registration_socket = context.socket(zmq.REP)
registration_socket.bind(f"tcp://*:{REGISTRATION_PORT}")

# Socket to handle group list requests
group_list_socket = context.socket(zmq.REP)
group_list_socket.bind(f"tcp://*:{GROUP_LIST_PORT}")

# Data structure to maintain the group information
groups = defaultdict(dict)  # {group_id: {'name': group_name, 'address': ip_address}}

def register_group(data):
    group_id = data['id']
    group_name = data['name']
    ip_address = data['address']
    if group_id not in groups:
        groups[group_id] = {'name': group_name, 'address': ip_address}
        print(f"JOIN REQUEST FROM {ip_address} [ID: {group_id}]")
        return SUCCESS
    else:
        return FAILURE

def get_group_list():
    return json.dumps([{group_id: group_info} for group_id, group_info in groups.items()])

def process_registration_requests():
    while True:
        # Wait for next request from group server
        message = registration_socket.recv_json()
        response = register_group(message)
        registration_socket.send_string(response)

def process_group_list_requests():
    while True:
        # Wait for next request from user
        message = group_list_socket.recv_string()
        if message == "GET_GROUP_LIST":
            response = get_group_list()
            group_list_socket.send_string(response)

if __name__ == "__main__":
    try:
        # Start processing registration and group list requests
        process_registration_requests()
        process_group_list_requests()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        registration_socket.close()
        group_list_socket.close()
        context.term()
