from datetime import datetime


class Voto:
    VALIDO = "VALIDO"
    BRANCO = "BRANCO"
    NULO = "NULO"

    def __init__(self, eleicao_id, cargo, eleitor_id,
                 candidato_id=None, tipo="VALIDO", data_hora=None, id=None):
        self.id = id
        self.eleicao_id = eleicao_id
        self.cargo = cargo
        self.eleitor_id = eleitor_id
        self.candidato_id = candidato_id
        self.tipo = tipo
        self.data_hora = data_hora or datetime.now().isoformat(sep=" ", timespec="seconds")