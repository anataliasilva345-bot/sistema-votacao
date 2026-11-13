"""Servidor de votação: sockets TCP + uma thread por urna conectada.

Execute na raiz do projeto (mesma pasta do main.py):
    python servidor.py

Protocolo: uma mensagem JSON por linha, nos dois sentidos.
  -> {"acao": "votar", "eleicao_id": 1, "cargo": "...", "titulo": "...",
      "numero": "13", "tipo": "VALIDO"}
  <- {"ok": true}   ou   {"ok": false, "erro": "mensagem"}

Só o servidor acessa as regras de votação e o banco. Um único Lock serializa
todas as requisições, então dois votos nunca são gravados ao mesmo tempo
(e a restrição UNIQUE (eleicao_id, cargo, eleitor_id) continua valendo).
"""
import base64
import itertools
import json
import os
import socket
import sys
import threading
import traceback

from controllers.auth_controller import AuthController
from controllers.eleicao_controller import EleicaoController
from controllers.voto_controller import VotoController

HOST = "0.0.0.0"   # aceita conexões de outros computadores da rede
PORTA = 5050

trava = threading.Lock()          # protege banco e controllers
eleicao_ctrl = EleicaoController()
voto_ctrl = VotoController()
_numero_urna = itertools.count(1)

# Só caminhos de foto que o próprio servidor já enviou (via eleitor/candidato)
# podem ser baixados: impede que um cliente peça qualquer arquivo do disco.
FOTOS_LIBERADAS = set()
TAM_MAX_FOTO = 5 * 1024 * 1024   # 5 MB


# ------------------------------------------------------------ serialização
def _foto(caminho):
    """Libera o caminho para download e devolve (caminho, versão).
    A versão (data de modificação) invalida o cache da urna se a foto mudar."""
    if not caminho or not os.path.isfile(caminho):
        return None, None
    FOTOS_LIBERADAS.add(caminho)
    return caminho, os.stat(caminho).st_mtime_ns


def _eleitor(e):
    if not e:
        return None
    foto, versao = _foto(e.foto)
    return {"id": e.id, "nome": e.nome, "titulo": e.titulo,
            "foto": foto, "foto_v": versao, "biometria": bool(e.biometria)}


def _candidato(c):
    if not c:
        return None
    foto, versao = _foto(c.foto)
    return {"id": c.id, "nome": c.nome, "numero": c.numero,
            "partido": c.partido, "cargo": c.cargo,
            "foto": foto, "foto_v": versao}


# ------------------------------------------------------------------ ações
def acao_eleicoes(_req):
    lista = []
    for e in eleicao_ctrl.listar():
        if not e.esta_aberta:
            continue
        aceitos = [c.id for cargo in e.cargos
                   for c in voto_ctrl.repo.listar_candidatos(cargo)
                   if e.aceita_candidato(c.id)]
        lista.append({"id": e.id, "descricao": e.descricao(),
                      "cargos": list(e.cargos), "aceitos": aceitos})
    return {"eleicoes": lista}


def acao_buscar_eleitor(req):
    return {"eleitor": _eleitor(voto_ctrl.buscar_eleitor(req.get("titulo", "")))}


def acao_buscar_candidato(req):
    return {"candidato": _candidato(
        voto_ctrl.buscar_candidato(req.get("numero", ""), req.get("cargo")))}


def acao_votar(req):
    eleicao = next((e for e in eleicao_ctrl.listar()
                    if e.id == req.get("eleicao_id")), None)
    if not eleicao:
        raise ValueError("Eleição não encontrada.")
    voto_ctrl.registrar_voto(
        eleicao, req.get("cargo"), req.get("titulo"),
        req.get("numero"), req.get("tipo", "VALIDO"))
    return {}


def acao_foto(req):
    caminho = req.get("caminho")
    if (not isinstance(caminho, str) or caminho not in FOTOS_LIBERADAS
            or not os.path.isfile(caminho)):
        raise ValueError("Foto não disponível.")
    if os.path.getsize(caminho) > TAM_MAX_FOTO:
        raise ValueError("Foto muito grande.")
    with open(caminho, "rb") as f:
        return {"dados": base64.b64encode(f.read()).decode("ascii")}


ACOES = {
    "foto": acao_foto,
    "eleicoes": acao_eleicoes,
    "buscar_eleitor": acao_buscar_eleitor,
    "buscar_candidato": acao_buscar_candidato,
    "votar": acao_votar,
}


def executar(req, nome_cliente):
    acao = req.get("acao")
    try:
        funcao = ACOES.get(acao)
        if funcao is None:
            raise ValueError("Ação desconhecida.")
        if acao == "foto":        # só lê arquivo: não precisa do Lock do banco
            return {"ok": True, **funcao(req)}
        with trava:
            if acao == "votar":
                print(f"[voto] {nome_cliente} -> eleição={req.get('eleicao_id')} "
                      f"cargo={req.get('cargo')} título={req.get('titulo')} "
                      f"tipo={req.get('tipo')}")
            # A auditoria usa AuthController.usuario_atual(); aqui ele passa a
            # identificar a urna que fez a requisição (seguro: estamos no Lock).
            AuthController._usuario_logado = nome_cliente
            try:
                resp = {"ok": True, **funcao(req)}
                if acao == "votar":
                    print(f"[voto] {nome_cliente} -> GRAVADO no banco")
                return resp
            finally:
                AuthController._usuario_logado = None
    except ValueError as ex:                 # regra de negócio (voto duplicado...)
        print(f"[recusado] {nome_cliente}: {ex}")
        return {"ok": False, "erro": str(ex)}
    except Exception:                        # bug inesperado: não derruba a thread
        traceback.print_exc()
        return {"ok": False, "erro": "Erro interno do servidor."}


# ------------------------------------------------------------ uma thread/cliente
def atender(conn, addr):
    nome = f"urna-{next(_numero_urna)}@{addr[0]}"
    print(f"[+] {nome} conectou")
    try:
        with conn, conn.makefile("rw", encoding="utf-8", newline="\n") as arq:
            for linha in arq:
                try:
                    req = json.loads(linha)
                    if not isinstance(req, dict):
                        raise json.JSONDecodeError("não é objeto", linha, 0)
                except json.JSONDecodeError:
                    resp = {"ok": False, "erro": "Mensagem inválida."}
                else:
                    resp = executar(req, nome)
                arq.write(json.dumps(resp, ensure_ascii=False) + "\n")
                arq.flush()
    except OSError:
        pass                                  # cliente caiu
    finally:
        print(f"[-] {nome} desconectou")


def _banner_banco():
    """Mostra QUAL arquivo de banco este servidor está usando e o que há nele.
    O admin (main.py) só enxerga os votos se usar exatamente este mesmo arquivo."""
    try:
        for nome, mod in list(sys.modules.items()):
            if nome.endswith("conexao") and hasattr(mod, "Conexao"):
                con = mod.Conexao().conn
                caminho = con.execute("PRAGMA database_list").fetchone()[2]
                print(f"Banco em uso : {caminho}")
                print(f"Votos gravados: {con.execute('SELECT COUNT(*) FROM votos').fetchone()[0]}"
                      f" | Auditoria: {con.execute('SELECT COUNT(*) FROM auditoria').fetchone()[0]} linhas")
                for r in con.execute("SELECT e.id, e.nome, e.status, "
                                     "(SELECT COUNT(*) FROM votos v WHERE v.eleicao_id=e.id) "
                                     "FROM eleicoes e ORDER BY e.id"):
                    print(f"   eleição #{r[0]} '{r[1]}' [{r[2]}] -> {r[3]} votos")
                return
    except Exception as ex:
        print(f"(não foi possível ler o banco para o diagnóstico: {ex})")


def main():
    _banner_banco()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORTA))
    srv.listen()
    srv.settimeout(1.0)   # acorda a cada 1s para o Ctrl+C funcionar no Windows
    print(f"Servidor de votação ouvindo na porta {PORTA} (Ctrl+C para parar)")
    try:
        while True:
            try:
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            threading.Thread(target=atender, args=(conn, addr),
                             daemon=True).start()
    except KeyboardInterrupt:
        print("\nEncerrando servidor.")
    finally:
        srv.close()


if __name__ == "__main__":
    main()
