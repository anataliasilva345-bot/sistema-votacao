from models.pessoa import Pessoa


class Eleitor(Pessoa):
    def __init__(self, nome, cpf, titulo, id=None, ja_votou=False,
                 foto=None, biometria=False):
        super().__init__(nome)
        self.id = id
        self.cpf = cpf
        self.titulo = titulo
        self.ja_votou = ja_votou
        self.foto = foto
        self.biometria = biometria

    def descricao(self) -> str:
        return f"Eleitor: {self.nome} | Título: {self.titulo}"

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "cpf": self.cpf,
                "titulo": self.titulo, "ja_votou": self.ja_votou,
                "foto": self.foto, "biometria": self.biometria}