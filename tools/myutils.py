import datetime
import hashlib
import json
import random
import re
import string
import time

class utils :
    @staticmethod
    def initialize():
      pass

    # 将字符串和当前时间的毫秒数作为种子
    @staticmethod
    def generate_seed(string):
        # 将当前时间的毫秒数转换为字符串，并追加到原始字符串后面
        string_with_time = string #+ str(int(round(time.time() * 1000)))

        # 使用SHA-256哈希函数计算字符串的哈希值
        hash_object = hashlib.sha256(string_with_time.encode())
        hash_hex = hash_object.hexdigest()

        # 将哈希值转换为一个32位的无符号整数作为种子
        seed = int(hash_hex, 16) % 2**32
        return seed

    @staticmethod
    def is_valid_seed(seed_str):
        """
        Check if a string is a valid seed.
        A valid seed must have the following properties:
        - Length must be 9.
        - Only digits are allowed.
        - The sum of digits must be even.
        """
        if len(seed_str) != 9:
            return False
        if not seed_str.isdigit():
            return False
        return True

    @staticmethod
    def get_friendkey(string):
        # 使用 SHA256 哈希函数计算输入字符串的哈希值
        h = hashlib.sha256(string.encode()).hexdigest()
        # 取哈希值前 8 位作为邀请码
        invite_code = h[:8]
        return "id_" +invite_code
    @staticmethod# 检查邀请码是否合法
    def is_valid_invite_code(invite_code):
        return re.match(utils.invite_code_pattern, invite_code) is not None
    @staticmethod# 检查礼物码是否合法
    def is_valid_gift_code(gift_code):
        return re.match(utils.gift_code_pattern, gift_code) is not None


    @staticmethod
    def generate_unique_time_string():#生成唯一的时间字符串
        # 获取当前时间并格式化为字符串
        current_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")

        # 生成一个随机字符串
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=5))

        # 将当前时间和随机字符串组合成一个唯一的字符串
        unique_time_string = f"{current_time}_{random_string}"

        return unique_time_string

    @staticmethod
    def generate_random_secret_key_string(length=32):
        import secrets
        import base64

        def generate_secret_key(length: length) -> str:
                return base64.urlsafe_b64encode(secrets.token_bytes(length)).decode("utf-8")

        SECRET_KEY = generate_secret_key(length)
        return SECRET_KEY

    @staticmethod
    def generate_int32_digit_number():
        return random.randint(1, 2**31 - 1)
    
    @staticmethod
    def generate_alphanumeric_string(length: int) -> str:
        chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))


def to_text(value, encoding="utf-8") -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return value.decode(encoding)
    return str(value)

def json_loads(s):
    s = to_text(s)
    return json.loads(s)


def json_dumps(d):
    return json.dumps(d)
