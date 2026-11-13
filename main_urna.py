"""Urna de votação em rede.

Uso:  python main_urna.py [ip_do_servidor] [porta]
Sem argumentos conecta em 127.0.0.1:5050. Pode abrir várias urnas ao mesmo tempo.
"""
import sys

import customtkinter as ctk

from rede import cliente_rede


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    porta = int(sys.argv[2]) if len(sys.argv) > 2 else cliente_rede.PORTA_PADRAO
    try:
        cliente_rede.conectar(host, porta)
    except OSError as ex:
        sys.exit(f"Não foi possível conectar em {host}:{porta} -> {ex}")

    # Importa depois de conectar: a TelaVotacao detecta a conexão e usa a rede.
    from views.tela_votacao import TelaVotacao

    janela = ctk.CTk()
    janela.title(f"Urna Eletrônica - servidor {host}:{porta}")
    janela.geometry("1000x720")
    TelaVotacao(janela).pack(fill="both", expand=True)
    janela.mainloop()


if __name__ == "__main__":
    main()
