# utils.py
import json
import os

import cryptography
from cryptography.fernet import Fernet

DATA_DIR = 'data'
CHAT_HISTORY_FILE = os.path.join(DATA_DIR, 'chat_history.json')
USER_CREDENTIALS_FILE = os.path.join(DATA_DIR, 'user_credentials.json')
KEY_FILE = os.path.join(DATA_DIR, 'secret.key')

def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as key_file:
        key_file.write(key)

def load_key():
    return open(KEY_FILE, 'rb').read()

# Generate key if it doesn't exist
if not os.path.exists(KEY_FILE):
    generate_key()

key = load_key()
cipher_suite = Fernet(key)

def encrypt_data(data):
    json_data = json.dumps(data).encode()
    encrypted_data = cipher_suite.encrypt(json_data)
    return encrypted_data

def decrypt_data(encrypted_data):
    try:
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
    except (cryptography.fernet.InvalidToken, TypeError) as e:
        print(f"Error decrypting data: {e}")
        return None

def load_history():
    try:
        with open(CHAT_HISTORY_FILE, 'rb') as file:
            encrypted_data = file.read()
        return decrypt_data(encrypted_data) or []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(messages):
    with open(CHAT_HISTORY_FILE, 'wb') as file:
        encrypted_data = encrypt_data(messages)
        file.write(encrypted_data)

def load_user_credentials():
    try:
        with open(USER_CREDENTIALS_FILE, 'rb') as file:
            encrypted_data = file.read()
        return decrypt_data(encrypted_data) or {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_credentials(credentials):
    with open(USER_CREDENTIALS_FILE, 'wb') as file:
        encrypted_data = encrypt_data(credentials)
        file.write(encrypted_data)
