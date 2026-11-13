import re
import unicodedata


def validar_cpf(cpf: str) -> bool:
    cpf = "".join(filter(str.isdigit, cpf or ""))
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    for i in range(9, 11):
        soma = sum(int(cpf[n]) * ((i + 1) - n) for n in range(i))
        dig = (soma * 10) % 11
        if dig == 10:
            dig = 0
        if dig != int(cpf[i]):
            return False
    return True


def normalizar_nome(nome: str) -> str:
    """Nome para comparação: sem acento, sem maiúsculas e sem espaços extras.
    "  José   da Silva " e "jose da silva" ficam iguais."""
    sem_acento = unicodedata.normalize("NFKD", nome or "")
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", sem_acento).strip().casefold()
