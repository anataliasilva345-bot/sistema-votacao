import customtkinter as ctk

from views import tema
from models.repositorio import Repositorio


class TelaInicio(ctk.CTkFrame):
    """Página inicial: cartões centrais com as mesmas opções da lateral + Sair."""

    LARG_CARTAO = 182
    ALT_CARTAO = 150
    COLUNAS = 4

    def __init__(self, master, usuario, cartoes, ao_sair):
        super().__init__(master, fg_color=tema.FUNDO)

        centro = ctk.CTkFrame(self, fg_color="transparent")
        centro.pack(expand=True)  # sem fill: fica centralizado na área

        ctk.CTkLabel(centro, text=f"Bem-vindo, {usuario}",
                     font=("Arial", 28, "bold"),
                     text_color=tema.AZUL_LOGO).pack()
        ctk.CTkLabel(centro, text="Escolha uma das opções abaixo para continuar",
                     font=("Arial", 13), text_color=tema.TEXTO_SUAVE
                     ).pack(pady=(2, 18))

        self._estatisticas(centro)

        grade = ctk.CTkFrame(centro, fg_color="transparent")
        grade.pack(pady=(10, 0))

        itens = list(cartoes) + [dict(
            icone="⏻", titulo="Sair", descricao="Encerrar a sessão atual",
            comando=ao_sair, perigo=True)]
        for i, item in enumerate(itens):
            cartao = self._cartao(grade, **item)
            cartao.grid(row=i // self.COLUNAS, column=i % self.COLUNAS,
                        padx=8, pady=8)

    # ------------------------------------------------------------ pedaços
    def _estatisticas(self, pai):
        try:
            est = Repositorio().estatisticas()
        except Exception:
            return
        faixa = ctk.CTkFrame(pai, fg_color="transparent")
        faixa.pack()
        dados = [("Eleitores", est["eleitores"]),
                 ("Candidatos", est["candidatos"]),
                 ("Eleições abertas", est["eleicoes_abertas"]),
                 ("Votos registrados", est["votos"])]
        for i, (rotulo, valor) in enumerate(dados):
            caixa = ctk.CTkFrame(faixa, corner_radius=12, fg_color=tema.AZUL_LOGO)
            caixa.grid(row=0, column=i, padx=6)
            ctk.CTkLabel(caixa, text=str(valor), font=("Arial", 20, "bold"),
                         text_color=tema.AMARELO).pack(padx=22, pady=(8, 0))
            ctk.CTkLabel(caixa, text=rotulo, font=("Arial", 11),
                         text_color=tema.AZUL_CLARO).pack(padx=22, pady=(0, 8))

    def _cartao(self, pai, icone, titulo, descricao, comando, perigo=False):
        cor_borda = tema.VERMELHO if perigo else tema.AMARELO
        cor_icone = tema.VERMELHO_CLARO if perigo else tema.AZUL_SUAVE
        cor_titulo = tema.VERMELHO if perigo else tema.AZUL_LOGO

        cartao = ctk.CTkFrame(pai, width=self.LARG_CARTAO, height=self.ALT_CARTAO,
                              cursor="hand2", **tema.CARD_MODERNO)
        cartao.pack_propagate(False)

        bolha = ctk.CTkFrame(cartao, width=54, height=54, corner_radius=27,
                             fg_color=cor_icone, cursor="hand2")
        bolha.pack(pady=(18, 8))
        bolha.pack_propagate(False)
        lbl_icone = ctk.CTkLabel(bolha, text=icone, font=("Segoe UI Emoji", 22),
                                 text_color=cor_titulo, cursor="hand2")
        lbl_icone.place(relx=0.5, rely=0.5, anchor="center")

        lbl_titulo = ctk.CTkLabel(cartao, text=titulo, font=("Arial", 15, "bold"),
                                  text_color=cor_titulo, cursor="hand2")
        lbl_titulo.pack()
        lbl_desc = ctk.CTkLabel(cartao, text=descricao, font=("Arial", 11),
                                text_color=tema.TEXTO_SUAVE, wraplength=150,
                                cursor="hand2")
        lbl_desc.pack(pady=(2, 0), padx=8)

        def _dentro():
            w = cartao.winfo_containing(*cartao.winfo_pointerxy())
            while w is not None:
                if w is cartao:
                    return True
                w = getattr(w, "master", None)
            return False

        def entrar(_e=None):
            cartao.configure(border_color=cor_borda, border_width=2)

        def sair(_e=None):
            if not _dentro():
                cartao.configure(border_color=tema.BORDA, border_width=1)

        for w in (cartao, bolha, lbl_icone, lbl_titulo, lbl_desc):
            w.bind("<Enter>", entrar, add="+")
            w.bind("<Leave>", sair, add="+")
            w.bind("<Button-1>", lambda _e: comando(), add="+")
        return cartao
