import socket
import threading
import json
from concurrent.futures import ThreadPoolExecutor
from utils import load_history, save_history, load_user_credentials, save_user_credentials


class Server:
    def __init__(self, host, port, max_workers=10, max_clients=5):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.messages = load_history()
        self.user_credentials = load_user_credentials()
        self.clients = {}
        self.clients_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.client_semaphore = threading.Semaphore(max_clients)
        print(f"Сервер прослуховує на {host}:{port} з лімітом потоків {max_workers} та лімітом клієнтів {max_clients}")

    def start_server(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Прийнято підключення від {client_address}")
            self.executor.submit(self.handle_client, client_socket)

    def handle_client(self, client_socket):
        with self.client_semaphore:
            print("Робота з новим клієнтом")
            try:
                message = client_socket.recv(1024).decode()
                message_data = json.loads(message)
                if message_data["type"] == "login":
                    self.handle_login(client_socket, message_data)
                elif message_data["type"] == "register":
                    self.handle_register(client_socket, message_data)

                self.client_listener(client_socket, message_data["username"])
            except Exception as e:
                print(f"Помилка обробки клієнта: {e}")
                client_socket.close()
            finally:
                print("Обробку клієнта завершено")

    def handle_login(self, client_socket, message_data):
        username = message_data["username"]
        password = message_data["password"]
        if username in self.user_credentials and self.user_credentials[username] == password:
            with self.clients_lock:
                self.clients[username] = client_socket
            client_socket.sendall(json.dumps({"status": "ok"}).encode())
        else:
            client_socket.sendall(json.dumps({"status": "error", "message": "Невірний логін або пароль"}).encode())

    def handle_register(self, client_socket, message_data):
        username = message_data["username"]
        password = message_data["password"]
        if username not in self.user_credentials:
            self.user_credentials[username] = password
            save_user_credentials(self.user_credentials)
            with self.clients_lock:
                self.clients[username] = client_socket
            client_socket.sendall(json.dumps({"status": "ok"}).encode())
        else:
            client_socket.sendall(json.dumps({"status": "error", "message": "Користувач вже існує"}).encode())

    def client_listener(self, client_socket, username):
        self.send_user_list_update()
        try:
            while True:
                message = client_socket.recv(1024).decode()
                if not message:
                    break
                message_data = json.loads(message)
                self.process_message(message_data, username)
        except Exception as e:
            print(f"Помилка обробки повідомлення: {e}")
        finally:
            with self.clients_lock:
                del self.clients[username]
            self.send_user_list_update()
            client_socket.close()

    def send_user_list_update(self):
        user_list_message = {
            "type": "user_list",
            "users": list(self.user_credentials.keys())
        }
        message = json.dumps(user_list_message) + "\n"
        with self.clients_lock:
            for client in self.clients.values():
                try:
                    client.sendall(message.encode())
                except Exception as e:
                    print(f"Помилка надсилання оновлення списку користувачів: {e}")

    def process_message(self, message_data, sender):
        message_type = message_data.get("type")
        if message_type == "message":
            recipient = message_data.get("to")
            if recipient:
                self.messages.append(message_data)
                save_history(self.messages)
                self.send_message_to_client(json.dumps(message_data), recipient)
            else:
                print(f"Не вказано отримувача для повідомлення від {sender}")
        elif message_type == "request_conversation":
            user = message_data.get("user")
            self.send_conversation(sender, user)

    def save_data(self):
        save_history(self.messages)
        save_user_credentials(self.user_credentials)

    def send_message_to_client(self, message, recipient):
        with self.clients_lock:
            if recipient in self.clients:
                try:
                    self.clients[recipient].sendall((message + "\n").encode())
                except Exception as e:
                    print(f"Помилка надсилання повідомлення до {recipient}: {e}")
            else:
                print(f"Отримувач {recipient} не знайдений")

    def send_conversation(self, sender, user):
        conversation = [msg for msg in self.messages if
                        (msg["from"] == sender and msg["to"] == user) or (msg["from"] == user and msg["to"] == sender)]
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
            if (message["from"] == user1 and message["to"] == user2) or (
                    message["from"] == user2 and message["to"] == user1):
                conversation.append(message)
        return conversation
