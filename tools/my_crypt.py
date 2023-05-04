import base64
import json

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


def encrypt_message(message_json, key):
    key = bytes(key, encoding='utf-8')

    cipher = AES.new(key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(pad(message_json.encode('utf-8'), AES.block_size))

    # 将密文转换为字符串
    encrypted_message = base64.b64encode(ciphertext).decode('utf-8')
    return encrypted_message

def decrypt_message(encrypted_message_base64, key):
    key = bytes(key, encoding='utf-8')
    try:
        # 将密文字符串转换为字节串
        ciphertext = base64.b64decode(encrypted_message_base64.encode('utf-8'))

        # 解密
        cipher = AES.new(key, AES.MODE_ECB)
        decrypted_message = unpad(cipher.decrypt(ciphertext), AES.block_size)

        return json.loads( decrypted_message.decode('utf-8'))
    except Exception as e:
        print(f"解密失败，错误原因：{e}")
        return None