import customtkinter as ctk

from views import tema
from models.repositorio import Repositorio


# acao -> (rótulo, cor do texto, cor de fundo da etiqueta)
ACOES = {
    "LOGIN": ("Login", tema.VERDE, tema.VERDE_CLARO),
    "LOGOUT": ("Logout", tema.TEXTO_SUAVE, tema.CINZA_SUAVE),
    "CRIAR_ELEITOR": ("Novo eleitor", tema.AZUL_ESCURO, tema.AZUL_SUAVE),
    "CRIAR_CANDIDATO": ("Novo candidato", tema.AZUL_ESCURO, tema.AZUL_SUAVE),
    "CRIAR_ELEICAO": ("Nova eleição", tema.AZUL_ESCURO, tema.AZUL_SUAVE),
    "CRIAR_USUARIO": ("Novo usuário", tema.AZUL_ESCURO, tema.AZUL_SUAVE),
    "REGISTRAR_VOTO": ("Voto registrado", tema.AMARELO_ESCURO, tema.AMARELO_CLARO),
    "ENCERRAR_ELEICAO": ("Eleição encerrada", tema.VERMELHO, tema.VERMELHO_CLARO),
}
TODAS = "Todas as ações"


def _estilo(acao):
    return ACOES.get(acao, (acao.replace("_", " ").capitalize(),
                            tema.TEXTO_SUAVE, tema.CINZA_SUAVE))


def _data_hora(texto):
    try:
        data, hora = texto.split(" ")
        a, m, d = data.split("-")
        return f"{d}/{m}/{a}", hora
    except Exception:
        return texto, ""


class TelaAuditoria(ctk.CTkFrame):
    POR_PAGINA = 40
    INTERVALO_MS = 2000   # a cada quantos ms consulta o banco (tempo real)

    def __init__(self, master):
        super().__init__(master, fg_color=tema.FUNDO)
        self._timer = None
        self.registros = self._carregar()
        self.filtrados = []
        self.exibidos = 0

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=24, pady=(20, 6))
        ctk.CTkLabel(topo, text="Log de Auditoria", font=("Arial", 24, "bold"),
                     text_color=tema.AZUL_LOGO).pack(side="left")
        self.lbl_total = ctk.CTkLabel(topo, text="", font=("Arial", 12),
                                      text_color=tema.TEXTO_SUAVE)
        self.lbl_total.pack(side="left", padx=14, pady=(8, 0))
        ctk.CTkButton(topo, text="↻  Atualizar", width=110, height=32,
                      command=self._atualizar, **tema.BOTAO).pack(side="right")
        ctk.CTkLabel(topo, text="● Ao vivo", font=("Arial", 12, "bold"),
                     text_color=tema.VERDE).pack(side="right", padx=(0, 12))

        self._resumo()

        # Filtros
        filtros = ctk.CTkFrame(self, **tema.CARD_MODERNO)
        filtros.pack(fill="x", padx=24, pady=(4, 10))
        self.busca = ctk.CTkEntry(filtros, placeholder_text="🔎  Buscar por usuário ou detalhes…",
                                  **tema.ENTRY)
        self.busca.pack(side="left", fill="x", expand=True, padx=(12, 8), pady=10)
        self.busca.bind("<KeyRelease>", lambda _e: self._aplicar())
        self.filtro = ctk.CTkOptionMenu(
            filtros, **tema.OPTION, width=190, command=lambda _v: self._aplicar(),
            values=[TODAS] + sorted({_estilo(r["acao"])[0] for r in self.registros}))
        self.filtro.set(TODAS)
        self.filtro.pack(side="right", padx=(0, 12), pady=10)

        self.lista = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lista.pack(fill="both", expand=True, padx=(18, 12), pady=(0, 12))
        self.lista.grid_columnconfigure(0, weight=1)

        self._aplicar()
        self._timer = self.after(self.INTERVALO_MS, self._auto_atualizar)

    def destroy(self):
        # para o ciclo automático ao sair da tela
        if self._timer:
            self.after_cancel(self._timer)
            self._timer = None
        super().destroy()

    # ------------------------------------------------------------- dados
    @staticmethod
    def _carregar():
        return [dict(r) for r in Repositorio().listar_auditoria(500)]

    @staticmethod
    def _assinatura(registros):
        # o log só cresce: o id do registro mais novo muda quando há novidade
        return registros[0]["id"] if registros else None

    def _atualizar(self):
        self._aplicar_registros(self._carregar())

    def _aplicar_registros(self, registros):
        self.registros = registros
        self._atualizar_resumo()
        self._atualizar_filtro()
        self._aplicar()

    def _auto_atualizar(self):
        if not self.winfo_exists():
            return
        try:
            novos = self._carregar()
            # só redesenha se houver registro novo (evita piscar e perder a rolagem)
            if self._assinatura(novos) != self._assinatura(self.registros):
                self._aplicar_registros(novos)
        except Exception:
            pass   # banco ocupado por outro processo: tenta no próximo ciclo
        self._timer = self.after(self.INTERVALO_MS, self._auto_atualizar)

    def _atualizar_filtro(self):
        opcoes = [TODAS] + sorted({_estilo(r["acao"])[0] for r in self.registros})
        atual = self.filtro.get()
        self.filtro.configure(values=opcoes)
        if atual not in opcoes:
            self.filtro.set(TODAS)

    def _resumo(self):
        faixa = ctk.CTkFrame(self, fg_color="transparent")
        faixa.pack(fill="x", padx=24, pady=(4, 8))
        self.kpis = {}
        itens = [("registros", "Registros", tema.AZUL_LOGO),
                 ("votos", "Votos registrados", tema.AMARELO_ESCURO),
                 ("logins", "Logins", tema.VERDE),
                 ("usuarios", "Usuários ativos", tema.AZUL)]
        for i, (chave, rotulo, cor) in enumerate(itens):
            faixa.grid_columnconfigure(i, weight=1, uniform="kpi")
            caixa = ctk.CTkFrame(faixa, **tema.CARD_MODERNO)
            caixa.grid(row=0, column=i, padx=(0 if i == 0 else 6, 0), sticky="ew")
            ctk.CTkFrame(caixa, width=4, height=34, corner_radius=2,
                         fg_color=cor).pack(side="left", padx=(12, 10), pady=12)
            col = ctk.CTkFrame(caixa, fg_color="transparent")
            col.pack(side="left", pady=8)
            self.kpis[chave] = ctk.CTkLabel(col, text="0", font=("Arial", 20, "bold"),
                                            text_color=cor, anchor="w")
            self.kpis[chave].pack(fill="x")
            ctk.CTkLabel(col, text=rotulo, font=("Arial", 11),
                         text_color=tema.TEXTO_SUAVE, anchor="w").pack(fill="x")
        self._atualizar_resumo()

    def _atualizar_resumo(self):
        valores = {
            "registros": len(self.registros),
            "votos": sum(1 for r in self.registros if r["acao"] == "REGISTRAR_VOTO"),
            "logins": sum(1 for r in self.registros if r["acao"] == "LOGIN"),
            "usuarios": len({r["usuario"] for r in self.registros}),
        }
        for chave, valor in valores.items():
            self.kpis[chave].configure(text=str(valor))

    def _aplicar(self):
        termo = self.busca.get().strip().lower()
        escolhida = self.filtro.get()
        self.filtrados = [
            r for r in self.registros
            if (escolhida == TODAS or _estilo(r["acao"])[0] == escolhida)
            and (not termo or termo in f"{r['usuario']} {r['detalhes']} "
                                       f"{_estilo(r['acao'])[0]}".lower())]
        for w in self.lista.winfo_children():
            w.destroy()
        self.exibidos = 0
        self.lbl_total.configure(text=f"{len(self.filtrados)} registro(s) encontrado(s)")
        if not self.filtrados:
            ctk.CTkLabel(self.lista, text="Nenhum registro encontrado.",
                         font=("Arial", 13), text_color=tema.TEXTO_SUAVE
                         ).grid(row=0, column=0, pady=40)
            return
        self._mais()

    def _mais(self):
        # remove o botão "carregar mais" anterior, se existir
        if getattr(self, "_btn_mais", None):
            self._btn_mais.destroy()
            self._btn_mais = None
        fim = min(self.exibidos + self.POR_PAGINA, len(self.filtrados))
        for i in range(self.exibidos, fim):
            self._linha(i, self.filtrados[i])
        self.exibidos = fim
        if fim < len(self.filtrados):
            self._btn_mais = ctk.CTkButton(
                self.lista, text=f"Carregar mais ({len(self.filtrados) - fim} restantes)",
                command=self._mais, height=36, **tema.BOTAO_AMARELO)
            self._btn_mais.grid(row=fim, column=0, pady=12)

    def _linha(self, i, r):
        rotulo, cor, fundo = _estilo(r["acao"])
        data, hora = _data_hora(r["data_hora"])

        cartao = ctk.CTkFrame(self.lista, corner_radius=12, fg_color=tema.CARD,
                              border_width=1, border_color=tema.BORDA)
        cartao.grid(row=i, column=0, sticky="ew", pady=4, padx=(0, 6))
        cartao.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(cartao, text=rotulo, width=140, height=28, corner_radius=14,
                     fg_color=fundo, text_color=cor, font=("Arial", 12, "bold")
                     ).grid(row=0, column=0, padx=(14, 12), pady=12)

        detalhes = r["detalhes"] or "—"
        ctk.CTkLabel(cartao, text=detalhes, anchor="w", justify="left",
                     wraplength=380, font=("Arial", 12), text_color=tema.TEXTO
                     ).grid(row=0, column=1, sticky="w", pady=10)

        lado = ctk.CTkFrame(cartao, fg_color="transparent")
        lado.grid(row=0, column=2, padx=(8, 16), pady=8, sticky="e")
        ctk.CTkLabel(lado, text=f"👤 {r['usuario']}", anchor="e",
                     font=("Arial", 12, "bold"), text_color=tema.AZUL_ESCURO
                     ).pack(anchor="e")
        ctk.CTkLabel(lado, text=f"{data}  •  {hora}", anchor="e",
                     font=("Arial", 11), text_color=tema.TEXTO_SUAVE
                     ).pack(anchor="e")
