import socket
import threading
import json
from utils import load_history, save_history, load_user_credentials, save_user_credentials

class Server:
    def __init__(self, host, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.messages = load_history()
        self.user_credentials = load_user_credentials()
        self.clients = {}
        print(f"Server listening on {host}:{port}")

    def start_server(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        message = client_socket.recv(1024).decode()
        message_data = json.loads(message)
        if message_data["type"] == "login":
            self.handle_login(client_socket, message_data)
        elif message_data["type"] == "register":
            self.handle_register(client_socket, message_data)

    def handle_login(self, client_socket, message_data):
        username = message_data["username"]
        password = message_data["password"]
        if username in self.user_credentials and self.user_credentials[username] == password:
            self.clients[username] = client_socket
            client_socket.sendall(json.dumps({"status": "ok"}).encode())
            threading.Thread(target=self.client_listener, args=(client_socket, username)).start()
        else:
            client_socket.sendall(json.dumps({"status": "error", "message": "Неверный логин или пароль"}).encode())

    def handle_register(self, client_socket, message_data):
        username = message_data["username"]
        password = message_data["password"]
        if username not in self.user_credentials:
            self.user_credentials[username] = password
            save_user_credentials(self.user_credentials)
            self.clients[username] = client_socket
            client_socket.sendall(json.dumps({"status": "ok"}).encode())
            threading.Thread(target=self.client_listener, args=(client_socket, username)).start()
        else:
            client_socket.sendall(json.dumps({"status": "error", "message": "Пользователь уже существует"}).encode())

    def client_listener(self, client_socket, username):
        self.send_user_list_update()

        while True:
            try:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                message_data = json.loads(message)
                self.process_message(message_data, username)
            except Exception as e:
                print(f"Error handling message: {e}")
                break

        del self.clients[username]
        self.send_user_list_update()
        client_socket.close()

    def send_user_list_update(self):
        user_list_message = {
            "type": "user_list",
            "users": list(self.user_credentials.keys())
        }
        message = json.dumps(user_list_message) + "\n"
        for client in self.clients.values():
            client.sendall(message.encode())

    def process_message(self, message_data, sender):
        message_type = message_data.get("type")
        if message_type == "message":
            recipient = message_data.get("to")
            if recipient:
                self.messages.append(message_data)
                save_history(self.messages)
                self.send_message_to_client(json.dumps(message_data), recipient)
            else:
                print(f"No recipient specified for message from {sender}")
        elif message_type == "request_conversation":
            user = message_data.get("user")
            self.send_conversation(sender, user)

    def save_data(self):
        save_history(self.messages)
        save_user_credentials(self.user_credentials)

    def send_message_to_client(self, message, recipient):
        if recipient in self.clients:
            try:
                self.clients[recipient].sendall((message + "\n").encode())
            except Exception as e:
                print(f"Error sending message to {recipient}: {e}")
        else:
            print(f"Recipient {recipient} not found")

    def send_conversation(self, sender, user):
        conversation = [msg for msg in self.messages if (msg["from"] == sender and msg["to"] == user) or (msg["from"] == user and msg["to"] == sender)]
        conversation_message = {
            "type": "conversations",
            "conversations": {user: conversation}
        }
        self.send_message_to_client(json.dumps(conversation_message), sender)

    def get_conversations(self):
        conversations = {}
        for message in self.messages:
            if message.get("type") == "message":
                participants = tuple(sorted([message["from"], message["to"]]))
                if participants not in conversations:
                    conversations[participants] = []
                conversations[participants].append(message)
        return conversations

    def get_messages_between(self, user1, user2):
        conversation = []
        for message in self.messages:
            if (message["from"] == user1 and message["to"] == user2) or (message["from"] == user2 and message["to"] == user1):
                conversation.append(message)
        return conversation
