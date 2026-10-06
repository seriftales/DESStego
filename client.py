import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import customtkinter as ctk 
import os
import utils
import sqlite3
import time

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 4096

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("DESSTEGO SECURE MESSENGER")
        self.root.geometry("850x600")
        
        self.client_socket = None
        self.username = ""
        self.password = ""
        self.selected_user = None 
        self.selected_image_path = None
        
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.init_login_ui()

    #Giriş yapan kullanıcıya özel bir yerel veritabanı oluştur
    def init_local_db(self):
        """Local DB storing messages for each user"""
        self.db_path = f"history_{self.username}.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS messages 
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           contact TEXT, 
                           sender TEXT, 
                           content TEXT, 
                           timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()

    def save_message(self, contact, sender, content):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (contact, sender, content) VALUES (?, ?, ?)", 
                       (contact, sender, content))
        conn.commit()
        conn.close()

    def load_chat_history(self, contact):
        self.chat_area.configure(state='normal')
        self.chat_area.delete('1.0', tk.END)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sender, content, timestamp FROM messages WHERE contact=? ORDER BY timestamp ASC", (contact,))
        for sender, content, ts in cursor.fetchall():
            display_name = "Me" if sender == self.username else sender
            self.chat_area.insert(tk.END, f"[{ts[11:16]}] {display_name}: {content}\n")
        
        self.chat_area.see(tk.END)
        self.chat_area.configure(state='disabled')

    def init_login_ui(self):
        self.login_frame = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        ctk.CTkLabel(self.login_frame, text="DESSTEGO", font=("Helvetica", 24, "bold")).grid(row=0, column=0, columnspan=2, pady=20)
        self.entry_username = ctk.CTkEntry(self.login_frame, placeholder_text="Username", width=200)
        self.entry_username.grid(row=1, column=0, columnspan=2, padx=20, pady=5)
        self.entry_password = ctk.CTkEntry(self.login_frame, show="*", placeholder_text="Password", width=200)
        self.entry_password.grid(row=2, column=0, columnspan=2, padx=20, pady=5)
        
        ctk.CTkButton(self.login_frame, text="Select Image", command=self.select_image).grid(row=3, column=0, columnspan=2, pady=10)
        self.lbl_img_status = ctk.CTkLabel(self.login_frame, text="No image selected", text_color="gray")
        self.lbl_img_status.grid(row=4, column=0, columnspan=2)
        
        ctk.CTkButton(self.login_frame, text="Register", command=self.register_action, fg_color="#1f538d").grid(row=5, column=0, pady=20, padx=10)
        ctk.CTkButton(self.login_frame, text="Login", command=self.login_action, fg_color="#2ecc71").grid(row=5, column=1, pady=20, padx=10)

    def init_chat_ui(self):
        self.login_frame.destroy()
        self.init_local_db()
        
        # --- SIDEBAR (Tabbed) ---
        self.sidebar = ctk.CTkFrame(self.main_container, width=250, corner_radius=0)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        self.tabview = ctk.CTkTabview(self.sidebar, width=230)
        self.tabview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tabview.add("Active")
        self.tabview.add("All")
        
        self.list_active = tk.Listbox(self.tabview.tab("Active"), bg="#2b2b2b", fg="white", borderwidth=0, highlightthickness=0)
        self.list_active.pack(fill=tk.BOTH, expand=True)
        self.list_active.bind('<<ListboxSelect>>', lambda e: self.on_user_selected(self.list_active))
        
        self.list_all = tk.Listbox(self.tabview.tab("All"), bg="#2b2b2b", fg="white", borderwidth=0, highlightthickness=0)
        self.list_all.pack(fill=tk.BOTH, expand=True)
        self.list_all.bind('<<ListboxSelect>>', lambda e: self.on_user_selected(self.list_all))
        
        ctk.CTkButton(self.sidebar, text="Refresh", command=self.refresh_users).pack(pady=10)

        # --- CHAT AREA ---
        self.chat_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.chat_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.lbl_chat_with = ctk.CTkLabel(self.chat_container, text="Select a user to chat", font=("Helvetica", 16, "bold"))
        self.lbl_chat_with.pack(pady=(0, 10))
        
        self.chat_area = scrolledtext.ScrolledText(self.chat_container, state='disabled', bg="#333333", fg="white")
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        input_row = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        input_row.pack(fill=tk.X)
        self.entry_msg = ctk.CTkEntry(input_row, placeholder_text="Type your message...")
        self.entry_msg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry_msg.bind("<Return>", lambda e: self.send_message())
        ctk.CTkButton(input_row, text="Send", command=self.send_message, width=100).pack(side=tk.RIGHT)

    def on_user_selected(self, listbox):
        selection = listbox.curselection()
        if selection:
            self.selected_user = listbox.get(selection[0])
            self.lbl_chat_with.configure(text=f"Chatting with: {self.selected_user}")
            self.load_chat_history(self.selected_user)

    def send_message(self):
        if not self.selected_user:
            messagebox.showwarning("Warning", "Please select a user first!")
            return
        msg = self.entry_msg.get()
        if msg:
            enc = utils.des_encrypt(msg, self.password)
            self.client_socket.send(f"MSG {self.selected_user} {enc}".encode('utf-8'))
            self.save_message(self.selected_user, self.username, msg)
            self.load_chat_history(self.selected_user) 
            self.entry_msg.delete(0, tk.END)

    def listen_server(self):
        while True:
            try:
                data = self.client_socket.recv(BUFFER_SIZE).decode('utf-8')
                if not data: break
                
                if data.startswith("INCOMING"):
                    _, sender, enc = data.split(' ', 2)
                    plain = utils.des_decrypt(enc, self.password)
                    self.save_message(sender, sender, plain)
                    
                    if self.selected_user == sender:
                        self.load_chat_history(sender)
                    else:
                        print(f"New message from: {sender}")
                        
                elif data.startswith("LIST_RESULT"):
                    content = data.split(' ', 1)[1]
                    all_u_str, active_u_str = content.split('|')
                    
                    self.list_all.delete(0, tk.END)
                    for u in all_u_str.split(','):
                        if u and u != self.username: self.list_all.insert(tk.END, u)
                        
                    self.list_active.delete(0, tk.END)
                    for u in active_u_str.split(','):
                        if u and u != self.username: self.list_active.insert(tk.END, u)
            except Exception as e:
                print(f"[!] Sunucu ile bağlantı koptu veya hata oluştu: {e}")
                break

    def select_image(self):
        path = filedialog.askopenfilename()
        if path:
            self.selected_image_path = path
            self.lbl_img_status.configure(text=f"Image: {os.path.basename(path)}", text_color="cyan")

    def connect_socket(self):
        if not self.client_socket:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))

    def register_action(self):
        user, pwd = self.entry_username.get(), self.entry_password.get()
        if not user or len(pwd) != 8 or not self.selected_image_path:
            messagebox.showerror("Error", "Missing information or invalid password length!")
            return
        try:
            self.connect_socket()
            stego = "temp_stego.png"
            utils.hide_key_in_image(self.selected_image_path, pwd, stego)
            self.client_socket.send(f"REGISTER {user} {os.path.getsize(stego)}".encode('utf-8'))
            if "READY" in self.client_socket.recv(1024).decode('utf-8'):
                with open(stego, "rb") as f: self.client_socket.sendall(f.read())
                if "AUTH_OK" in self.client_socket.recv(1024).decode('utf-8'):
                    self.username, self.password = user, pwd
                    self.init_chat_ui()
                    threading.Thread(target=self.listen_server, daemon=True).start()
                    self.refresh_users()
            os.remove(stego)
        except Exception as e: messagebox.showerror("Error", str(e))

    def login_action(self):
        user, pwd = self.entry_username.get(), self.entry_password.get()
        if not user or not pwd: return
        try:
            self.connect_socket()
            self.client_socket.send(f"LOGIN {user} {pwd}".encode('utf-8'))
            if "AUTH_OK" in self.client_socket.recv(1024).decode('utf-8'):
                self.username, self.password = user, pwd
                self.init_chat_ui()
                threading.Thread(target=self.listen_server, daemon=True).start()
                self.refresh_users()
            else: messagebox.showerror("Error", "Login failed! Please check your credentials.")
        except Exception as e: messagebox.showerror("Error", str(e))

    def refresh_users(self):
        if self.client_socket: self.client_socket.send("LIST".encode('utf-8'))

if __name__ == "__main__":
    root = ctk.CTk()
    app = ChatClient(root)
    root.mainloop()