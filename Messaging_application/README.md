# Using ZeroMQ to Low-Level Group Messaging Application

## Pre-setup Requirements:
- Ensure Python is installed on your system.
- Install ZeroMQ library using pip:
```bash
pip install pyzmq
```

## Running the Application:

1. Start the Message Server:
```bash
python message_server.py
```

2. Start Group Servers:
```bash
python group.py <group_name> <message_server_endpoint> <group_ip> <group_port>
```

example:
```bash
python group.py Group1 tcp://34.28.43.43:5555 34.173.21.231 5556
```

3. Start User Clients:
```bash
python user_client.py <message_server_endpoint>
```

example:
```bash
python user_client.py tcp://34.28.43.43:5555
```

## Usage:
When using user_client's menu driven interface, make sure to always enter the complete address of group servers when asked (example: tcp://34.173.21.231:5556) and follow the exact requested formats.