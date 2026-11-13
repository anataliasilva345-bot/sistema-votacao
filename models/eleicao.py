class Eleicao:
    def __init__(self, nome, cargos, status="ABERTA", id=None, candidatos_ids=None):
        """cargos: lista de strings, ex.: ["Presidente", "Senador"].
        candidatos_ids: ids dos candidatos que participam desta eleição.
        Lista vazia = eleição antiga (criada antes da seleção de candidatos),
        em que qualquer candidato do cargo é aceito."""
        if not cargos:
            raise ValueError("Eleição precisa de ao menos um cargo.")
        self.id = id
        self.nome = nome
        self.cargos = list(cargos)
        self.candidatos_ids = list(candidatos_ids or [])
        self._status = status

    @property
    def status(self):
        return self._status

    def encerrar(self):
        self._status = "ENCERRADA"

    def abrir(self):
        self._status = "ABERTA"

    @property
    def esta_aberta(self) -> bool:
        return self._status == "ABERTA"

    def aceita_candidato(self, candidato_id) -> bool:
        """True se o candidato participa desta eleição."""
        return not self.candidatos_ids or candidato_id in self.candidatos_ids

    def descricao(self) -> str:
        qtd = (f" | Candidatos: {len(self.candidatos_ids)}"
               if self.candidatos_ids else "")
        return (f"Eleição: {self.nome} | Cargos: {', '.join(self.cargos)}"
                f"{qtd} | Status: {self._status}")
