import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import customtkinter as ctk 
import os
import utils
import time

# Görünüm Ayarları
ctk.set_appearance_mode("dark")  # Sistem temasına göre "light" da yapılabilir
ctk.set_default_color_theme("blue")

# Server Bilgileri 
HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 4096

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("DESSTEGO SECURE CHAT")
        self.root.geometry("700x550") # Biraz genişlettim daha ferah durması için
        
        self.client_socket = None
        self.username = ""
        self.password = ""
        self.selected_image_path = None
        
        # Ana Konteynır (Arka plan rengi için)
        self.main_container = ctk.CTkFrame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.init_login_ui()
        
    def init_login_ui(self):
        self.login_frame = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.login_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        ctk.CTkLabel(self.login_frame, text="DESSTEGO LOGIN", font=("Helvetica", 20, "bold")).grid(row=0, column=0, columnspan=2, pady=20)
        
        ctk.CTkLabel(self.login_frame, text="Username:").grid(row=1, column=0, padx=20, pady=5, sticky="e")
        self.entry_username = ctk.CTkEntry(self.login_frame, placeholder_text="Username", width=200)
        self.entry_username.grid(row=1, column=1, padx=20, pady=5)
        
        ctk.CTkLabel(self.login_frame, text="Password:").grid(row=2, column=0, padx=20, pady=5, sticky="e")
        self.entry_password = ctk.CTkEntry(self.login_frame, show="*", placeholder_text="8 Characters", width=200)
        self.entry_password.grid(row=2, column=1, padx=20, pady=5)
        
        self.btn_select_img = ctk.CTkButton(self.login_frame, text="Select Image", command=self.select_image, fg_color="transparent", border_width=2)
        self.btn_select_img.grid(row=3, column=0, columnspan=2, pady=15)
        
        self.lbl_img_status = ctk.CTkLabel(self.login_frame, text="No image selected", text_color="orange")
        self.lbl_img_status.grid(row=4, column=0, columnspan=2, pady=5)
        
        self.btn_register = ctk.CTkButton(self.login_frame, text="Register", command=self.register_action, fg_color="#1f538d", hover_color="#14375e")
        self.btn_register.grid(row=5, column=0, pady=20, padx=10)
        
        self.btn_login = ctk.CTkButton(self.login_frame, text="Login", command=self.login_action, fg_color="#2ecc71", hover_color="#27ae60")
        self.btn_login.grid(row=5, column=1, pady=20, padx=10)

    def init_chat_ui(self):
        self.login_frame.destroy()
        
        # Sidebar (Sol Panel)
        self.sidebar_frame = ctk.CTkFrame(self.main_container, width=200, corner_radius=0)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ctk.CTkLabel(self.sidebar_frame, text="Online Users", font=("Helvetica", 14, "bold")).pack(pady=20)
        
        # Standart Listbox (CTK içinde en stabil bu çalışır, rengini uydurdum)
        self.user_listbox = tk.Listbox(self.sidebar_frame, bg="#2b2b2b", fg="white", borderwidth=0, highlightthickness=0, font=("Helvetica", 11))
        self.user_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.btn_refresh = ctk.CTkButton(self.sidebar_frame, text="Refresh", command=self.refresh_users, height=30)
        self.btn_refresh.pack(pady=10, padx=10)
        
        # Chat Alanı (Sağ Panel)
        self.chat_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.chat_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_area = scrolledtext.ScrolledText(self.chat_container, state='disabled', bg="#333333", fg="white", font=("Helvetica", 11), borderwidth=0)
        self.chat_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        input_row = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        input_row.pack(fill=tk.X)
        
        self.entry_msg = ctk.CTkEntry(input_row, placeholder_text="Type a message...", height=40)
        self.entry_msg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry_msg.bind("<Return>", lambda event: self.send_message())
        
        self.btn_send = ctk.CTkButton(input_row, text="Send", command=self.send_message, width=100, height=40)
        self.btn_send.pack(side=tk.RIGHT)

    # --- MANTIK KISMI (DEĞİŞMEDİ) ---

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")])
        if path:
            self.selected_image_path = path
            self.lbl_img_status.configure(text=f"Selected: {os.path.basename(path)}", text_color="cyan")

    def connect_socket(self):
        if not self.client_socket:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((HOST, PORT))

    def register_action(self):
        user, pwd = self.entry_username.get(), self.entry_password.get()
        if not user or len(pwd) != 8 or not self.selected_image_path:
            messagebox.showerror("Hata", "Tüm alanları doldurun ve resim seçin!"); return
        
        try:
            self.connect_socket()
            stego_name = "temp_stego.png"
            utils.hide_key_in_image(self.selected_image_path, pwd, stego_name)
            filesize = os.path.getsize(stego_name)
            self.client_socket.send(f"REGISTER {user} {filesize}".encode('utf-8'))
            
            if "READY" in self.client_socket.recv(1024).decode('utf-8'):
                with open(stego_name, "rb") as f:
                    while True:
                        chunk = f.read(BUFFER_SIZE)
                        if not chunk: break
                        self.client_socket.send(chunk)
                
                res = self.client_socket.recv(1024).decode('utf-8')
                if "AUTH_OK" in res:
                    self.username, self.password = user, pwd
                    self.init_chat_ui()
                    threading.Thread(target=self.listen_server, daemon=True).start()
                else: messagebox.showerror("Hata", res)
            if os.path.exists(stego_name): os.remove(stego_name)
        except Exception as e: messagebox.showerror("Hata", str(e))

    def login_action(self):
        user, pwd = self.entry_username.get(), self.entry_password.get()
        if not user or not pwd: return
        
        try:
            self.connect_socket()
            self.client_socket.send(f"LOGIN {user} {pwd}".encode('utf-8'))
            res = self.client_socket.recv(1024).decode('utf-8')
            if "AUTH_OK" in res:
                self.username, self.password = user, pwd
                self.init_chat_ui()
                threading.Thread(target=self.listen_server, daemon=True).start()
                self.refresh_users()
            else: messagebox.showerror("Hata", "Giriş başarısız!")
        except Exception as e: messagebox.showerror("Hata", str(e))

    def send_message(self):
        try:
            selection = self.user_listbox.curselection()
            if not selection:
                messagebox.showwarning("Uyarı", "Önce listeden birini seç!")
                return
            target = self.user_listbox.get(selection[0])
            msg = self.entry_msg.get()
            
            if msg:
                enc = utils.des_encrypt(msg, self.password)
                payload = f"MSG {target} {enc}"
                self.client_socket.send(payload.encode('utf-8'))
                self.add_log(f"Ben -> {target}: {msg}")
                self.entry_msg.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Hata", f"Mesaj gönderilemedi: {e}")
    
    def refresh_users(self):
        if self.client_socket: self.client_socket.send("LIST".encode('utf-8'))

    def listen_server(self):
        while True:
            try:
                data = self.client_socket.recv(BUFFER_SIZE).decode('utf-8')
                if not data: break
                if data.startswith("INCOMING"):
                    parts = data.split(' ', 2)
                    if len(parts) >= 3:
                        sender, enc = parts[1], parts[2]
                        plain = utils.des_decrypt(enc, self.password)
                        self.add_log(f"{sender}: {plain}")
                elif data.startswith("LIST_RESULT"):
                    parts = data.split(' ', 1)
                    if len(parts) > 1:
                        self.user_listbox.delete(0, tk.END)
                        for u in parts[1].split(','):
                            if u != self.username:
                                self.user_listbox.insert(tk.END, u)
            except: break

    def add_log(self, text):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, text + "\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

if __name__ == "__main__":
    # Tk yerine CTK kullandık
    root = ctk.CTk() 
    app = ChatClient(root)
    root.mainloop()