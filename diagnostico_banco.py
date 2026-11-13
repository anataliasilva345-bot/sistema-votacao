"""Mostra o que há dentro de cada votacao.db do projeto.

Uso: python diagnostico_banco.py            (procura sozinho a partir desta pasta)
     python diagnostico_banco.py CAMINHO    (ou informe o arquivo/pasta)
Só lê o banco: pode rodar com o sistema aberto.
"""
import datetime
import os
import sqlite3
import sys


def achar_bancos(base):
    if os.path.isfile(base):
        return [base]
    achados = []
    for pasta, _dirs, arquivos in os.walk(base):
        if "votacao.db" in arquivos:
            achados.append(os.path.join(pasta, "votacao.db"))
    return achados


def mostrar(caminho):
    print("=" * 70)
    print("Arquivo:", os.path.abspath(caminho))
    print("Modificado em:", datetime.datetime.fromtimestamp(
        os.path.getmtime(caminho)).strftime("%d/%m/%Y %H:%M:%S"))
    c = sqlite3.connect(f"file:{os.path.abspath(caminho)}?mode=ro", uri=True)
    print("\nEleições:")
    for r in c.execute("SELECT e.id, e.nome, e.status, "
                       "(SELECT COUNT(*) FROM votos v WHERE v.eleicao_id=e.id) "
                       "FROM eleicoes e"):
        print(f"  #{r[0]} {r[1]} [{r[2]}] -> {r[3]} votos")
    print("\nÚltimas 10 linhas da auditoria:")
    for r in c.execute("SELECT id, data_hora, usuario, acao FROM auditoria "
                       "ORDER BY id DESC LIMIT 10"):
        print("  ", r)
    print("\nÚltimos 10 votos:")
    for r in c.execute("SELECT id, eleicao_id, cargo, tipo, data_hora FROM votos "
                       "ORDER BY id DESC LIMIT 10"):
        print("  ", r)
    c.close()


alvo = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
bancos = achar_bancos(alvo)
if not bancos:
    sys.exit(f"Nenhum votacao.db encontrado em {alvo}")
print(f"Encontrado(s) {len(bancos)} banco(s).")
if len(bancos) > 1:
    print("ATENÇÃO: há mais de um votacao.db no projeto — só um deles é o usado!")
for b in bancos:
    mostrar(b)
