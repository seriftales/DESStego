import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import utils
import time

HOST = '127.0.0.1'
PORT = 12345
BUFFER_SIZE = 4096

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Güvenli Chat İstemcisi (LSB & DES)")
        self.root.geometry("600x550")
        
        self.client_socket = None
        self.username = ""
        self.password = ""
        self.selected_image_path = None
        self.init_login_ui()
        
    def init_login_ui(self):
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(pady=20)
        
        tk.Label(self.login_frame, text="Kullanıcı Adı:").grid(row=0, column=0, pady=5)
        self.entry_username = tk.Entry(self.login_frame)
        self.entry_username.grid(row=0, column=1, pady=5)
        
        tk.Label(self.login_frame, text="Parola (8 Karakter):").grid(row=1, column=0, pady=5)
        self.entry_password = tk.Entry(self.login_frame, show="*")
        self.entry_password.grid(row=1, column=1, pady=5)
        
        # Resim Seçme (Sadece Kayıt İçin Gerekli)
        tk.Button(self.login_frame, text="Resim Seç (Sadece Kayıt)", command=self.select_image).grid(row=2, column=0, columnspan=2, pady=10)
        self.lbl_img_status = tk.Label(self.login_frame, text="Resim seçilmedi", fg="red")
        self.lbl_img_status.grid(row=3, column=0, columnspan=2)
        
        # İki Ayrı Buton: Kayıt ve Giriş
        tk.Button(self.login_frame, text="Kayıt Ol (Resimle)", command=self.register_action, bg="blue", fg="white").grid(row=4, column=0, pady=10, padx=5)
        tk.Button(self.login_frame, text="Giriş Yap (Şifreyle)", command=self.login_action, bg="green", fg="white").grid(row=4, column=1, pady=10, padx=5)

    def init_chat_ui(self):
        """Senin Orijinal Geniş Chat Ekranın"""
        self.login_frame.destroy()
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sol Taraf: Kullanıcı Listesi (Sidebar)
        left_frame = tk.Frame(main_frame, width=150)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        tk.Label(left_frame, text="Aktif Kullanıcılar").pack()
        self.user_listbox = tk.Listbox(left_frame)
        self.user_listbox.pack(fill=tk.BOTH, expand=True)
        tk.Button(left_frame, text="Yenile", command=self.refresh_users).pack(pady=5)
        
        # Sağ Taraf: Chat Alanı
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        self.chat_area = scrolledtext.ScrolledText(right_frame, state='disabled')
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        
        input_frame = tk.Frame(right_frame)
        input_frame.pack(fill=tk.X, pady=5)
        tk.Label(input_frame, text="Mesaj:").pack(side=tk.LEFT)
        self.entry_msg = tk.Entry(input_frame)
        self.entry_msg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        tk.Button(input_frame, text="Gönder", command=self.send_message).pack(side=tk.RIGHT)

    def select_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")])
        if path:
            self.selected_image_path = path
            self.lbl_img_status.config(text=f"Seçildi: {os.path.basename(path)}", fg="blue")

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
        # Listbox'tan seçili kullanıcıyı al
        try:
            selection = self.user_listbox.curselection()
            if not selection:
                messagebox.showwarning("Uyarı", "Önce listeden birini seç!")
                return
            target = self.user_listbox.get(selection[0])
            msg = self.entry_msg.get()
            
            if msg:
                # Kendi şifrenle şifreleyip sunucuya gönder
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
                
                # Gelen veriyi güvenli parçala
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
            except:
                print("Bağlantı koptu.")
                break

    def add_log(self, text):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, text + "\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk(); app = ChatClient(root); root.mainloop()