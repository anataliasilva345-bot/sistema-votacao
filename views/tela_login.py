import customtkinter as ctk
from views import tema
from controllers.auth_controller import AuthController


class TelaLogin(ctk.CTk):
    def __init__(self, ao_logar):
        super().__init__()
        self.ao_logar = ao_logar
        self.ctrl = AuthController()

        self.title("Login — Sistema de Votação")
        self.geometry("460x560")
        tema.configurar()
        self.configure(fg_color=tema.FUNDO)

        tema.faixa(self).pack(side="bottom", fill="x")

        topo = ctk.CTkFrame(self, corner_radius=0, fg_color=tema.AZUL_LOGO)
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text="", image=tema.logo(340)).pack(pady=24)

        ctk.CTkLabel(self, text="Acesso do administrador",
                     font=("Arial", 14, "bold"),
                     text_color=tema.AZUL_ESCURO).pack(pady=(24, 0))

        self.usuario = ctk.CTkEntry(self, placeholder_text="Usuário", width=280, **tema.ENTRY)
        self.usuario.pack(pady=(18, 8))

        self.senha = ctk.CTkEntry(self, placeholder_text="Senha", show="*", width=280, **tema.ENTRY)
        self.senha.pack(pady=8)

        ctk.CTkButton(self, text="Entrar", command=self.entrar, width=280, height=38, **tema.BOTAO).pack(pady=12)

        self.msg = ctk.CTkLabel(self, text="", text_color=tema.VERMELHO)
        self.msg.pack()

        self.senha.bind("<Return>", lambda _e: self.entrar())


    def entrar(self):
        try:
            self.ctrl.login(self.usuario.get().strip(), self.senha.get())
            self.destroy()
            self.ao_logar()
        except Exception as ex:
            self.msg.configure(text=str(ex))