# DESStego Secure Messenger

DESStego, kriptografi (DES) ve steganografiyi aynı mimaride buluşturan, eğitim ve algoritma analizi amacıyla geliştirilmiş bir mesajlaşma uygulamasıdır.

Uygulama, kullanıcıların şifreleme anahtarlarını resim dosyalarının içine gömerek kayıt olmalarını ve aralarında şifreli mesajlaşmalarını sağlayan bir İstemci-Sunucu mimarisi sunar. Modern ve kullanıcı dostu arayüzü `customtkinter` ile tasarlanmıştır.


## 🚀 Özellikler

* **LSB Steganografi:** Kullanıcıların gizli DES anahtarları, `Pillow` kütüphanesi kullanılarak LSB yöntemiyle `.jpg` dosyalarının içine gizlenir.
* **DES Şifreleme:** İstemciler arası mesajlaşma paketleri, `pycryptodome` kullanılarak ECB modunda DES ile şifrelenir.
* **Çoklu İstemci:** Sunucu, aynı anda birden fazla istemciyi `threading` modülü ile asenkron olarak idare eder ve çevrimdışı mesajları veritabanında bekletir.
* **Yerel Mesaj Geçmişi:** Her istemci, kendi sohbet geçmişini lokaldedeki SQLite veritabanında saklar.

## 🛠️ Kurulum (Linux)

Not:Sisteminizde `python3-tk` (Tkinter) paketinin işletim sistemi seviyesinde kurulu olduğundan emin olun.

```bash
sudo apt update
sudo apt install python3-tk -y
```
Projenin bağımlılıklarının izole edilmesi için sanal ortam (venv) kullanılması tavsiye edilir. 

1. **Depoyu Klonlayın:**
   ```bash
   git clone [https://github.com/seriftales/DESStego.git](https://github.com/seriftales/DESStego.git)
   cd DESStego
   ```
2. **Sanal Ortam (venv) kurun ve aktive edin:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Bağımlılıkları yükleyin:**
  ```bash
  pip install -r requirements.txt
  ```

## ⚙️ Çalıştırma

1. **Sunucuyu Başlatın:**
Merkezi yönlendirmeyi sağlamak için önce sunucuyu ayağa kaldırın:
```bash
    python3 server.py
```
2. **İstemcileri Başlatın:**
Farklı terminaller açarak mesajlaşmayı test etmek için istemcileri başlatın:
```bash
   source venv/bin/activate
   python3 client.py
```
Kayıt olurken bir resim dosyası seçmeniz ve 8 karakterlik bir şifre belirlemeniz zorunludur.

## 📁 Dizin Yapısı 
```text
DESStego/
├── client.py         # CustomTkinter arayüzlü mesajlaşma istemcisi
├── server.py         # Multi-threaded paket yönlendirici ve veritabanı yöneticisi
├── utils.py          # LSB steganografi ve DES kriptografi motoru
├──/pictures          # LSB steganografi uygulanacak görüntüleri barındıran klasör  
├── requirements.txt  # Proje bağımlılıkları 
└── README.md         
└──.gitignore
```
