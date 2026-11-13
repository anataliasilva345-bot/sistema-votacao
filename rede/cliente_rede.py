"""Cliente de rede da urna.

Expõe EleicaoControllerRede e VotoControllerRede com os mesmos métodos que a
TelaVotacao já usa nos controllers locais, então a tela quase não muda.
"""
import base64
import hashlib
import json
import os
import socket
import tempfile
import threading
from types import SimpleNamespace

PORTA_PADRAO = 5050
PASTA_CACHE = os.path.join(tempfile.gettempdir(), "urna_cache_fotos")

_cliente = None


class ClienteRede:
    def __init__(self, host, porta=PORTA_PADRAO, timeout=5):
        self.sock = socket.create_connection((host, porta), timeout=timeout)
        self.arq = self.sock.makefile("rw", encoding="utf-8", newline="\n")
        self._trava = threading.Lock()

    def chamar(self, **requisicao):
        """Envia uma requisição e devolve a resposta.
        ValueError = erro de regra vindo do servidor; ConnectionError = rede."""
        with self._trava:
            try:
                self.arq.write(json.dumps(requisicao, ensure_ascii=False) + "\n")
                self.arq.flush()
                linha = self.arq.readline()
            except OSError as ex:
                raise ConnectionError("Sem conexão com o servidor.") from ex
        if not linha:
            raise ConnectionError("O servidor encerrou a conexão.")
        resp = json.loads(linha)
        if not resp.get("ok"):
            raise ValueError(resp.get("erro", "Erro desconhecido."))
        return resp

    def fechar(self):
        try:
            self.arq.close()
            self.sock.close()
        except OSError:
            pass


def conectar(host="127.0.0.1", porta=PORTA_PADRAO):
    global _cliente
    _cliente = ClienteRede(host, porta)
    return _cliente


def conectado():
    return _cliente is not None


# ---------------------------------------------------------------- fotos
def _foto_local(d):
    """Baixa a foto do servidor (uma vez) e devolve o caminho da cópia local."""
    caminho = d.get("foto")
    if not caminho:
        return None
    chave = hashlib.sha1(caminho.encode("utf-8")).hexdigest()
    ext = os.path.splitext(caminho)[1].lower()
    destino = os.path.join(PASTA_CACHE, f"{chave}_{d.get('foto_v')}{ext}")
    if not os.path.isfile(destino):
        try:
            dados = base64.b64decode(
                _cliente.chamar(acao="foto", caminho=caminho)["dados"])
        except ValueError:
            return None            # sem foto: a tela mostra o avatar padrão
        os.makedirs(PASTA_CACHE, exist_ok=True)
        tmp = destino + ".tmp"
        with open(tmp, "wb") as f:
            f.write(dados)
        os.replace(tmp, destino)
    return destino


def _como_objeto(d):
    if not d:
        return None
    d = dict(d)
    d["foto"] = _foto_local(d)
    d.pop("foto_v", None)
    return SimpleNamespace(**d)


# ---------------------------------------------------------------- adaptadores
class EleicaoRemota:
    """Imita o necessário do modelo Eleicao usado pela tela."""

    def __init__(self, d):
        self.id = d["id"]
        self.cargos = d["cargos"]
        self.esta_aberta = True
        self._descricao = d["descricao"]
        self._aceitos = set(d["aceitos"])

    def descricao(self):
        return self._descricao

    def aceita_candidato(self, candidato_id):
        return candidato_id in self._aceitos


class EleicaoControllerRede:
    def listar(self):
        resp = _cliente.chamar(acao="eleicoes")
        return [EleicaoRemota(d) for d in resp["eleicoes"]]


class VotoControllerRede:
    def buscar_eleitor(self, titulo):
        titulo = str(titulo).strip()
        if not titulo:
            return None
        return _como_objeto(
            _cliente.chamar(acao="buscar_eleitor", titulo=titulo)["eleitor"])

    def buscar_candidato(self, numero, cargo=None):
        numero = str(numero).strip()
        if not numero.isdigit():
            return None
        return _como_objeto(_cliente.chamar(
            acao="buscar_candidato", numero=numero, cargo=cargo)["candidato"])

    def registrar_voto(self, eleicao, cargo, titulo_eleitor,
                       numero_candidato=None, tipo="VALIDO"):
        _cliente.chamar(acao="votar", eleicao_id=eleicao.id, cargo=cargo,
                        titulo=titulo_eleitor, numero=numero_candidato,
                        tipo=tipo)
