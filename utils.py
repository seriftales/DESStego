import binascii
from Crypto.Cipher import DES
from PIL import Image

#Verilen düz metni (plaintext) DES algoritması (ECB Modu) ile şifreler.
def des_encrypt(message, key):
    if len(key) != 8:
        raise ValueError("DES Anahtarı tam olarak 8 karakter olmalıdır!")
    while len(message) % 8 != 0:
        message += ' '
    des = DES.new(key.encode('utf-8'), DES.MODE_ECB)
    encrypted_data = des.encrypt(message.encode('utf-8'))
    return binascii.hexlify(encrypted_data).decode('utf-8')

#Hexadecimal formatta gelen şifreli metni DES anahtarı ile çözer.
def des_decrypt(encrypted_hex, key):
    if len(key) != 8:
        raise ValueError("DES Anahtarı tam olarak 8 karakter olmalıdır!")
    try:
        des = DES.new(key.encode('utf-8'), DES.MODE_ECB)
        encrypted_data = binascii.unhexlify(encrypted_hex)
        decrypted_data = des.decrypt(encrypted_data).decode('utf-8')
        return decrypted_data.rstrip() 
    except Exception as e:
        return f"Şifre Çözme Hatası: {e}"

def text_to_bits(text):
    bits = bin(int(binascii.hexlify(text.encode('utf-8')), 16))[2:]
    return bits.zfill(8 * ((len(bits) + 7) // 8))

#LSB steganografi yöntemini kullanarak anahtarı bir resmin RGB piksellerinin en anlamsız bitlerine gömer.
def hide_key_in_image(image_path, secret_key, output_path):
    img = Image.open(image_path)
    if img.mode != 'RGB': img = img.convert('RGB')
    encoded = img.copy()
    width, height = img.size
    full_secret = secret_key + "#####"
    secret_bits = text_to_bits(full_secret)
    data_len = len(secret_bits)
    data_index = 0
    pixels = encoded.load()
    for y in range(height):
        for x in range(width):
            if data_index < data_len:
                r, g, b = pixels[x, y]
                bit_to_hide = int(secret_bits[data_index])
                r = (r & 0xFE) | bit_to_hide
                pixels[x, y] = (r, g, b)
                data_index += 1
            else: break
        if data_index >= data_len: break
    encoded.save(output_path)
    return True

#İşlenmiş resmin piksellerini tarayarak LSB yöntemiyle gizlenmiş bitleri toplar.
def extract_key_from_image(image_path):
    img = Image.open(image_path)
    if img.mode != 'RGB': img = img.convert('RGB')
    width, height = img.size
    pixels = img.load()
    current_bits = ""
    decoded_text = ""
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            current_bits += str(r & 1)
            if len(current_bits) == 8:
                try:
                    char = chr(int(current_bits, 2))
                    decoded_text += char
                except: pass
                current_bits = ""
                if decoded_text.endswith("#####"):
                    return decoded_text[:-5]
    return None