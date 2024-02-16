# Install RabbitMQ
```
sudo apt-get update
sudo apt-get install -y rabbitmq-server

sudo systemctl enable rabbitmq-server
sudo systemctl start rabbitmq-server
```

# Create a new user (replace 'newuser' and 'newpassword' with your desired username and password)
```
sudo rabbitmqctl add_user newuser newpassword
```

# Set permissions for the user (replace 'newuser' with your username)
```
sudo rabbitmqctl set_user_tags newuser administrator
sudo rabbitmqctl set_permissions -p / newuser ".*" ".*" ".*"
```
# Activate Virtual Python Environment on Server Instance 1
```
source myenv/bin/activate
python3 YoutubeServer.py
```

# Activate Virtual Python Environment on Server Instance 2 (Example)
```
source myenv/bin/activate
python3 User.py username s TomScott
python3 Youtuber.py TomScott Ten Years of my Life
```
