import sqlite3
import os

USUARIOS_PADRAO = [
    ("admin", "admin123", "ADMIN"),
    ("maria", "maria123", "ADMIN"),   # novo administrador
]


class Conexao:
    _instancia = None

    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            # Variável de ambiente VOTACAO_DB permite forçar um único arquivo
            # para o servidor e o admin.
            caminho = os.environ.get("VOTACAO_DB") or os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "votacao.db")
            # check_same_thread=False: o servidor de rede usa a conexão a
            # partir de várias threads, sempre protegido por um threading.Lock.
            cls._instancia.conn = sqlite3.connect(
                caminho, check_same_thread=False, timeout=10)
            # WAL: o admin pode ler enquanto o servidor grava (sem "database is locked")
            cls._instancia.conn.execute("PRAGMA journal_mode=WAL")
            cls._instancia.conn.row_factory = sqlite3.Row
            cls._instancia._criar_tabelas()
            cls._instancia._migrar()
            cls._instancia._criar_admin_padrao()
        return cls._instancia

    def _criar_tabelas(self):
        caminho_sql = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(caminho_sql, "r", encoding="utf-8") as f:
            self.conn.executescript(f.read())
            self.conn.commit()

    def _migrar(self):
        colunas = [r[1] for r in self.conn.execute("PRAGMA table_info(candidatos)")]
        if "foto" not in colunas:
            self.conn.execute("ALTER TABLE candidatos ADD COLUMN foto TEXT")
            self.conn.commit()

        colunas = [r[1] for r in self.conn.execute("PRAGMA table_info(eleitores)")]
        if "foto" not in colunas:
            self.conn.execute("ALTER TABLE eleitores ADD COLUMN foto TEXT")
        if "biometria" not in colunas:
            self.conn.execute(
                "ALTER TABLE eleitores ADD COLUMN biometria INTEGER NOT NULL DEFAULT 0")
        self.conn.commit()

    def _criar_admin_padrao(self):
        """Garante que cada usuário de USUARIOS_PADRAO exista (sem apagar o banco)."""
        from utils.seguranca import hash_senha
        for usuario, senha, papel in USUARIOS_PADRAO:
            existe = self.conn.execute(
                "SELECT 1 FROM usuarios WHERE usuario = ?", (usuario,)
            ).fetchone()
            if not existe:
                salt, h = hash_senha(senha)
                self.conn.execute(
                    "INSERT INTO usuarios (usuario, senha_hash, salt, papel) "
                    "VALUES (?,?,?,?)",
                    (usuario, h, salt, papel))
        self.conn.commit()

    def executar(self, sql, parametros=()):
        cur = self.conn.cursor()
        cur.execute(sql, parametros)
        self.conn.commit()
        return cur

    def consultar(self, sql, parametros=()):
        cur = self.conn.cursor()
        cur.execute(sql, parametros)
        return cur.fetchall()

    def fechar(self):
        self.conn.close()