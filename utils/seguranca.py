import hashlib
import secrets


def hash_senha(senha: str, salt: str | None = None):
    """Retorna (salt, hash_hex). Se salt=None gera um novo."""
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + senha).encode("utf-8")).hexdigest()
    return salt, h


def verificar_senha(senha: str, salt: str, hash_armazenado: str) -> bool:
    _, h = hash_senha(senha, salt)
    return h == hash_armazenado