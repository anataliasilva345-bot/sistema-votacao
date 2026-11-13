import customtkinter as ctk

from views import tema

from views.tela_inicio import TelaInicio
from views.tela_eleitores import TelaEleitores
from views.tela_candidatos import TelaCandidatos
from views.tela_eleicao import TelaEleicao
from views.tela_votacao import TelaVotacao
from views.tela_resultados import TelaResultados
from views.tela_auditoria import TelaAuditoria
from controllers.auth_controller import AuthController


class App(ctk.CTk):
    # chave, ícone, título, descrição (usada nos cartões da tela Início)
    MENU = [
        ("eleitores", "👥", "Eleitores", "Cadastre e consulte os eleitores"),
        ("candidatos", "🏅", "Candidatos", "Candidatos, números e partidos"),
        ("eleicoes", "📅", "Eleições", "Crie e encerre eleições"),
        ("votar", "📥", "Votar", "Urna eletrônica de votação"),
        ("resultados", "📊", "Resultados", "Apuração, fotos e relatórios"),
        ("auditoria", "🛡", "Auditoria", "Histórico de ações do sistema"),
    ]

    def __init__(self):
        # 🔒 Bloqueio de segurança: só instancia com usuário autenticado.
        if AuthController.usuario_atual() == "anonimo":
            raise RuntimeError(
                "Acesso negado: faça login antes de abrir a aplicação."
            )

        super().__init__()
        self.title("Sistema de Votação Eletrônica")
        self.geometry("1180x720")
        self.minsize(1060, 640)
        tema.configurar()
        self.configure(fg_color=tema.FUNDO)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.telas = {
            "inicio": lambda: TelaInicio(
                self.area, AuthController.usuario_atual(),
                self._cartoes_inicio(), self.logout),
            "eleitores": lambda: TelaEleitores(self.area),
            "candidatos": lambda: TelaCandidatos(self.area),
            "eleicoes": lambda: TelaEleicao(self.area),
            "votar": lambda: TelaVotacao(self.area),
            "resultados": lambda: TelaResultados(self.area),
            "auditoria": lambda: TelaAuditoria(self.area),
        }

        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0,
                                    fg_color=tema.SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.pack_propagate(False)

        self.area = ctk.CTkFrame(self, corner_radius=0, fg_color=tema.FUNDO)
        self.area.grid(row=0, column=1, sticky="nsew")

        self._montar_sidebar()

        self.tela_atual = None
        self.navegar("inicio")

    # ------------------------------------------------------------ sidebar
    def _montar_sidebar(self):
        sb = self.sidebar
        self.itens = {}

        # Rodapé (empacotado primeiro para ficar sempre visível embaixo)
        rodape = ctk.CTkFrame(sb, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=14, pady=(8, 16))

        usuario = AuthController.usuario_atual()
        cartao = ctk.CTkFrame(rodape, corner_radius=12, fg_color=tema.SIDEBAR_HOVER)
        cartao.pack(fill="x", pady=(0, 10))
        avatar = ctk.CTkFrame(cartao, width=38, height=38, corner_radius=19,
                              fg_color=tema.AMARELO)
        avatar.pack(side="left", padx=(10, 10), pady=10)
        avatar.pack_propagate(False)
        ctk.CTkLabel(avatar, text=usuario[:1].upper(), text_color=tema.AZUL_LOGO,
                     font=("Arial", 16, "bold")).place(relx=0.5, rely=0.5,
                                                       anchor="center")
        textos = ctk.CTkFrame(cartao, fg_color="transparent")
        textos.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(textos, text=usuario, anchor="w", text_color="white",
                     font=("Arial", 13, "bold")).pack(fill="x")
        ctk.CTkLabel(textos, text="Administrador", anchor="w",
                     text_color=tema.SIDEBAR_TEXTO,
                     font=("Arial", 11)).pack(fill="x")

        ctk.CTkButton(rodape, text="⏻   Sair", command=self.logout, height=40,
                      anchor="w", font=("Arial", 13, "bold"),
                      fg_color="#3A1D2B", hover_color=tema.VERMELHO,
                      text_color="#FFB4AB", corner_radius=10).pack(fill="x")

        # Topo
        ctk.CTkLabel(sb, text="", image=tema.logo(200)).pack(pady=(18, 6), padx=10)
        ctk.CTkFrame(sb, height=3, width=60, corner_radius=2,
                     fg_color=tema.AMARELO).pack(pady=(0, 18))

        ctk.CTkLabel(sb, text="NAVEGAÇÃO", anchor="w", text_color="#6F82A5",
                     font=("Arial", 10, "bold")).pack(fill="x", padx=24, pady=(0, 6))

        self._criar_item("inicio", "🏠", "Início")
        for chave, icone, titulo, _desc in self.MENU:
            self._criar_item(chave, icone, titulo)

    def _criar_item(self, chave, icone, texto):
        linha = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        linha.pack(fill="x", padx=(8, 14), pady=2)

        indicador = ctk.CTkFrame(linha, width=4, height=30, corner_radius=2,
                                 fg_color="transparent")
        indicador.pack(side="left", padx=(0, 6))

        botao = ctk.CTkButton(
            linha, text=f"{icone}   {texto}", anchor="w", height=42,
            font=("Arial", 13), corner_radius=10,
            fg_color="transparent", hover_color=tema.SIDEBAR_HOVER,
            text_color=tema.SIDEBAR_TEXTO,
            command=lambda: self.navegar(chave))
        botao.pack(side="left", fill="x", expand=True)
        self.itens[chave] = (indicador, botao)

    def _marcar_ativo(self, chave):
        for k, (indicador, botao) in self.itens.items():
            ativo = k == chave
            indicador.configure(fg_color=tema.AMARELO if ativo else "transparent")
            botao.configure(
                fg_color=tema.SIDEBAR_ATIVO if ativo else "transparent",
                text_color="white" if ativo else tema.SIDEBAR_TEXTO,
                font=("Arial", 13, "bold" if ativo else "normal"))

    # ---------------------------------------------------------- navegação
    def navegar(self, chave):
        self._marcar_ativo(chave)
        if self.tela_atual:
            self.tela_atual.destroy()
        self.tela_atual = self.telas[chave]()
        self.tela_atual.pack(fill="both", expand=True)

    def _cartoes_inicio(self):
        return [dict(icone=icone, titulo=titulo, descricao=desc,
                     comando=lambda c=chave: self.navegar(c))
                for chave, icone, titulo, desc in self.MENU]

    # Atalhos mantidos por compatibilidade
    def abrir_inicio(self):     self.navegar("inicio")
    def abrir_eleitores(self):  self.navegar("eleitores")
    def abrir_candidatos(self): self.navegar("candidatos")
    def abrir_eleicoes(self):   self.navegar("eleicoes")
    def abrir_votacao(self):    self.navegar("votar")
    def abrir_resultados(self): self.navegar("resultados")
    def abrir_auditoria(self):  self.navegar("auditoria")

    def logout(self):
        AuthController().logout()
        self.destroy()
        from views.tela_login import TelaLogin
        from views.app import App
        login = TelaLogin(ao_logar=lambda: App().mainloop())
        login.mainloop()
