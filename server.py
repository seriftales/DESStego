import socket
import threading
import os
import sqlite3
import utils
import time

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 4096
online_clients = {}

def init_db():
    conn = sqlite3.connect('chat_server.db')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, secret_key TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS offline_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT, receiver TEXT, encrypted_content TEXT)')
    conn.commit()
    conn.close()

def handle_client(client_socket, addr):
    current_user = None
    try:
        while True:
            raw_data = client_socket.recv(BUFFER_SIZE)
            if not raw_data: break
            
            data = raw_data.decode('utf-8')
            parts = data.split(' ', 2)
            command = parts[0]

            if command == "REGISTER":
                username, filesize = parts[1], int(parts[2])
                client_socket.send("READY_TO_RECEIVE".encode('utf-8'))
                img_data = b""
                while len(img_data) < filesize:
                    chunk = client_socket.recv(min(filesize - len(img_data), BUFFER_SIZE))
                    if not chunk: break
                    img_data += chunk
                
                temp_name = f"srv_{username}.png"
                with open(temp_name, "wb") as f: f.write(img_data)
                extracted_key = utils.extract_key_from_image(temp_name)
                if os.path.exists(temp_name): os.remove(temp_name)

                if extracted_key:
                    conn = sqlite3.connect('chat_server.db')
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?)", (username, extracted_key))
                    conn.commit()
                    conn.close()
                    current_user = username
                    online_clients[username] = client_socket
                    client_socket.send("AUTH_OK".encode('utf-8'))
                else:
                    client_socket.send("AUTH_FAIL".encode('utf-8'))

            elif command == "LOGIN":
                username, password = parts[1], parts[2]
                conn = sqlite3.connect('chat_server.db')
                cursor = conn.cursor()
                cursor.execute("SELECT secret_key FROM users WHERE username=? AND secret_key=?", (username, password))
                if cursor.fetchone():
                    current_user = username
                    online_clients[username] = client_socket
                    client_socket.send("AUTH_OK".encode('utf-8'))
                    
                    cursor.execute("SELECT sender, encrypted_content FROM offline_messages WHERE receiver=?", (username,))
                    for s, m in cursor.fetchall():
                        client_socket.send(f"INCOMING {s} {m}".encode('utf-8'))
                        time.sleep(0.1)
                    cursor.execute("DELETE FROM offline_messages WHERE receiver=?", (username,))
                    conn.commit()
                else:
                    client_socket.send("AUTH_FAIL".encode('utf-8'))
                conn.close()

            elif command == "MSG" and current_user:
                target_user, encrypted_msg = parts[1], parts[2]
                conn = sqlite3.connect('chat_server.db')
                cursor = conn.cursor()
                cursor.execute("SELECT secret_key FROM users WHERE username=?", (current_user,))
                s_key = cursor.fetchone()[0]
                cursor.execute("SELECT secret_key FROM users WHERE username=?", (target_user,))
                t_row = cursor.fetchone()
                
                if t_row:
                    t_key = t_row[0]
                    plain = utils.des_decrypt(encrypted_msg, s_key)
                    re_enc = utils.des_encrypt(plain, t_key)
                    
                    if target_user in online_clients:
                        try:
                            online_clients[target_user].send(f"INCOMING {current_user} {re_enc}".encode('utf-8'))
                        except:
                            cursor.execute("INSERT INTO offline_messages (sender, receiver, encrypted_content) VALUES (?, ?, ?)", (current_user, target_user, re_enc))
                            conn.commit()
                    else:
                        cursor.execute("INSERT INTO offline_messages (sender, receiver, encrypted_content) VALUES (?, ?, ?)", (current_user, target_user, re_enc))
                        conn.commit()
                conn.close()

            elif command == "LIST":
                conn = sqlite3.connect('chat_server.db')
                cursor = conn.cursor()
                # Tüm kullanıcılar
                cursor.execute("SELECT username FROM users")
                all_users = [r[0] for r in cursor.fetchall()]
                # Aktif kullanıcılar
                active_users = list(online_clients.keys())
                
                payload = f"LIST_RESULT {','.join(all_users)}|{','.join(active_users)}"
                client_socket.send(payload.encode('utf-8'))
                conn.close()

    except: pass
    finally:
        if current_user in online_clients: del online_clients[current_user]
        client_socket.close()

def start_server():
    init_db()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT)); server.listen(5)
    print(f"[*] Server Active: {HOST}:{PORT}")
    while True:
        c, a = server.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()

if __name__ == "__main__":
    start_server()