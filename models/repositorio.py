from database.conexao import Conexao
from models.eleitor import Eleitor
from models.candidato import Candidato
from models.eleicao import Eleicao
from models.voto import Voto


class Repositorio:
    def __init__(self):
        self.db = Conexao()

    # ---------------- USUÁRIOS ----------------
    def buscar_usuario(self, usuario: str):
        rows = self.db.consultar(
            "SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
        return dict(rows[0]) if rows else None

    def inserir_usuario(self, usuario, senha_hash, salt, papel="ADMIN"):
        self.db.executar(
            "INSERT INTO usuarios (usuario, senha_hash, salt, papel) VALUES (?,?,?,?)",
            (usuario, senha_hash, salt, papel))

    # ---------------- ELEITORES ----------------
    @staticmethod
    def _eleitor(r):
        return Eleitor(r["nome"], r["cpf"], r["titulo"], r["id"],
                       bool(r["ja_votou"]), r["foto"], bool(r["biometria"]))

    def inserir_eleitor(self, e: Eleitor) -> int:
        cur = self.db.executar(
            "INSERT INTO eleitores (nome, cpf, titulo, ja_votou, foto, biometria) "
            "VALUES (?,?,?,?,?,?)",
            (e.nome, e.cpf, e.titulo, int(e.ja_votou), e.foto, int(e.biometria)))
        return cur.lastrowid

    def listar_eleitores(self):
        rows = self.db.consultar("SELECT * FROM eleitores ORDER BY nome")
        return [self._eleitor(r) for r in rows]

    def buscar_eleitor_por_titulo(self, titulo):
        rows = self.db.consultar("SELECT * FROM eleitores WHERE titulo = ?", (titulo,))
        if not rows:
            return None
        return self._eleitor(rows[0])

    def buscar_eleitor_por_id(self, eleitor_id):
        rows = self.db.consultar("SELECT * FROM eleitores WHERE id = ?", (eleitor_id,))
        return self._eleitor(rows[0]) if rows else None

    def buscar_eleitor_por_cpf(self, cpf):
        rows = self.db.consultar("SELECT * FROM eleitores WHERE cpf = ?", (cpf,))
        return self._eleitor(rows[0]) if rows else None

    def eleitor_tem_votos(self, eleitor_id) -> bool:
        return len(self.db.consultar(
            "SELECT 1 FROM votos WHERE eleitor_id = ? LIMIT 1", (eleitor_id,))) > 0

    def excluir_eleitor(self, eleitor_id):
        self.db.executar("DELETE FROM eleitores WHERE id = ?", (eleitor_id,))

    def marcar_eleitor_votou(self, eleitor_id):
        self.db.executar("UPDATE eleitores SET ja_votou = 1 WHERE id = ?", (eleitor_id,))

    # ---------------- CANDIDATOS ----------------
    def inserir_candidato(self, c: Candidato) -> int:
        cur = self.db.executar(
            "INSERT INTO candidatos (nome, numero, partido, cargo, votos, foto) VALUES (?,?,?,?,?,?)",
            (c.nome, c.numero, c.partido, c.cargo, c.votos, c.foto))
        return cur.lastrowid

    def listar_candidatos(self, cargo=None):
        if cargo:
            rows = self.db.consultar(
                "SELECT * FROM candidatos WHERE cargo = ? ORDER BY votos DESC", (cargo,))
        else:
            rows = self.db.consultar("SELECT * FROM candidatos ORDER BY votos DESC")
        return [Candidato(r["nome"], r["numero"], r["partido"], r["cargo"],
                          r["votos"], r["id"], r["foto"]) for r in rows]

    # ⬇⬇ NOVO — busca o candidato pelo par (número, cargo), que é a chave única
    def buscar_candidato_por_numero_e_cargo(self, numero, cargo):
        rows = self.db.consultar(
            "SELECT * FROM candidatos WHERE numero = ? AND cargo = ?",
            (numero, cargo))
        if not rows:
            return None
        r = rows[0]
        return Candidato(r["nome"], r["numero"], r["partido"], r["cargo"],
                         r["votos"], r["id"], r["foto"])

    # Mantido para consultas pontuais (ex.: exibir duplicidades de nº entre cargos)
    def listar_candidatos_por_numero(self, numero):
        rows = self.db.consultar(
            "SELECT * FROM candidatos WHERE numero = ? ORDER BY cargo", (numero,))
        return [Candidato(r["nome"], r["numero"], r["partido"], r["cargo"],
                          r["votos"], r["id"], r["foto"]) for r in rows]

    def buscar_candidato_por_id(self, candidato_id):
        rows = self.buscar_candidatos_por_ids([candidato_id])
        return rows[0] if rows else None

    def eleicoes_do_candidato(self, candidato_id):
        """Nomes das eleições em que o candidato foi incluído."""
        rows = self.db.consultar(
            "SELECT e.nome FROM eleicao_candidatos ec "
            "JOIN eleicoes e ON e.id = ec.eleicao_id "
            "WHERE ec.candidato_id = ? ORDER BY e.id", (candidato_id,))
        return [r["nome"] for r in rows]

    def candidato_tem_votos(self, candidato_id) -> bool:
        return len(self.db.consultar(
            "SELECT 1 FROM votos WHERE candidato_id = ? LIMIT 1", (candidato_id,))) > 0

    def excluir_candidato(self, candidato_id):
        self.db.executar("DELETE FROM candidatos WHERE id = ?", (candidato_id,))

    def buscar_candidatos_por_ids(self, ids):
        ids = list(ids)
        if not ids:
            return []
        marcas = ",".join("?" * len(ids))
        rows = self.db.consultar(
            f"SELECT * FROM candidatos WHERE id IN ({marcas}) ORDER BY numero", ids)
        return [Candidato(r["nome"], r["numero"], r["partido"], r["cargo"],
                          r["votos"], r["id"], r["foto"]) for r in rows]

    def incrementar_voto_candidato(self, candidato_id):
        self.db.executar(
            "UPDATE candidatos SET votos = votos + 1 WHERE id = ?", (candidato_id,))

    # ---------------- ELEIÇÕES ----------------
    def inserir_eleicao(self, el: Eleicao) -> int:
        cur = self.db.executar(
            "INSERT INTO eleicoes (nome, status) VALUES (?,?)",
            (el.nome, el.status))
        eid = cur.lastrowid
        for cargo in el.cargos:
            self.db.executar(
                "INSERT INTO eleicao_cargos (eleicao_id, cargo) VALUES (?,?)",
                (eid, cargo))
        for cid in el.candidatos_ids:
            self.db.executar(
                "INSERT OR IGNORE INTO eleicao_candidatos (eleicao_id, candidato_id) "
                "VALUES (?,?)", (eid, cid))
        el.id = eid
        return eid

    def listar_eleicoes(self):
        rows = self.db.consultar("SELECT * FROM eleicoes ORDER BY id DESC")
        resultado = []
        for r in rows:
            cargos = [x["cargo"] for x in self.db.consultar(
                "SELECT cargo FROM eleicao_cargos WHERE eleicao_id = ?", (r["id"],))]
            cands = [x["candidato_id"] for x in self.db.consultar(
                "SELECT candidato_id FROM eleicao_candidatos WHERE eleicao_id = ?",
                (r["id"],))]
            resultado.append(Eleicao(r["nome"], cargos, r["status"], r["id"], cands))
        return resultado

    def atualizar_status_eleicao(self, eleicao_id, status):
        self.db.executar(
            "UPDATE eleicoes SET status = ? WHERE id = ?", (status, eleicao_id))

    # ---------------- VOTOS ----------------
    def inserir_voto(self, v: Voto) -> int:
        cur = self.db.executar(
            "INSERT INTO votos (eleicao_id, cargo, eleitor_id, candidato_id, tipo, data_hora) "
            "VALUES (?,?,?,?,?,?)",
            (v.eleicao_id, v.cargo, v.eleitor_id, v.candidato_id, v.tipo, v.data_hora))
        return cur.lastrowid

    def eleitor_ja_votou_no_cargo(self, eleicao_id, cargo, eleitor_id) -> bool:
        rows = self.db.consultar(
            "SELECT 1 FROM votos WHERE eleicao_id=? AND cargo=? AND eleitor_id=?",
            (eleicao_id, cargo, eleitor_id))
        return len(rows) > 0

    def total_votos(self, eleicao_id, cargo=None, tipo=None):
        sql = "SELECT COUNT(*) AS total FROM votos WHERE eleicao_id = ?"
        params = [eleicao_id]
        if cargo:
            sql += " AND cargo = ?"
            params.append(cargo)
        if tipo:
            sql += " AND tipo = ?"
            params.append(tipo)
        return self.db.consultar(sql, tuple(params))[0]["total"]

    def votos_por_candidato(self, eleicao_id, cargo):
        """Votos válidos de cada candidato NESTA eleição/cargo: {candidato_id: qtd}.
        Brancos e nulos têm candidato_id NULL e ficam de fora."""
        rows = self.db.consultar(
            "SELECT candidato_id, COUNT(*) AS qtd FROM votos "
            "WHERE eleicao_id = ? AND cargo = ? AND tipo = 'VALIDO' "
            "AND candidato_id IS NOT NULL GROUP BY candidato_id",
            (eleicao_id, cargo))
        return {r["candidato_id"]: r["qtd"] for r in rows}

    # ---------------- ESTATÍSTICAS ----------------
    def estatisticas(self):
        def _n(sql):
            return self.db.consultar(sql)[0][0]
        return {
            "eleitores": _n("SELECT COUNT(*) FROM eleitores"),
            "candidatos": _n("SELECT COUNT(*) FROM candidatos"),
            "eleicoes_abertas": _n(
                "SELECT COUNT(*) FROM eleicoes WHERE status = 'ABERTA'"),
            "votos": _n("SELECT COUNT(*) FROM votos"),
        }

    # ---------------- AUDITORIA ----------------
    def registrar_auditoria(self, usuario, acao, detalhes=""):
        from datetime import datetime
        self.db.executar(
            "INSERT INTO auditoria (data_hora, usuario, acao, detalhes) VALUES (?,?,?,?)",
            (datetime.now().isoformat(sep=" ", timespec="seconds"),
             usuario, acao, detalhes))

    def listar_auditoria(self, limite=200):
        return self.db.consultar(
            "SELECT * FROM auditoria ORDER BY id DESC LIMIT ?", (limite,))