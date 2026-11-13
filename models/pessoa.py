from abc import ABC, abstractmethod


class Pessoa(ABC):
    """Classe base abstrata para Eleitor e Candidato."""

    def __init__(self, nome: str):
        if not nome or not nome.strip():
            raise ValueError("Nome não pode ser vazio.")
        self._nome = nome.strip()

    @property
    def nome(self):
        return self._nome

    @abstractmethod
    def descricao(self) -> str:
        """Cada subclasse implementa seu próprio texto descritivo."""
        ...

    def __str__(self):
        return self.descricao()