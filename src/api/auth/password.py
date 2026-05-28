"""Auth 模块 - 密码哈希与验证。"""
import bcrypt as _bcrypt


def hash_password(password: str) -> str:
    """对密码进行 bcrypt 哈希。"""
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """验证密码与哈希是否匹配。"""
    try:
        return _bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, AttributeError):
        return False
