from models.pessoa import Pessoa


class Candidato(Pessoa):
    def __init__(self, nome, numero, partido, cargo, votos=0, id=None, foto=None):
        super().__init__(nome)
        self.id = id
        self.numero = numero
        self.partido = partido
        self.cargo = cargo
        self.votos = votos
        self.foto = foto

    def descricao(self) -> str:
        return (f"Candidato {self.numero} - {self.nome} "
                f"({self.partido}) | {self.cargo} | Votos: {self.votos}")

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "numero": self.numero,
                "partido": self.partido, "cargo": self.cargo,
                "votos": self.votos, "foto": self.foto}