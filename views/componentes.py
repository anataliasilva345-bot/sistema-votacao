import time
import tkinter as tk

import customtkinter as ctk

from views import tema


class BotaoBiometria(ctk.CTkFrame):
    """Leitor de digital SIMULADO.

    O usuário mantém o botão pressionado (mouse ou clique do touchpad) até
    o anel de progresso fechar. Não lê impressão digital real: serve como
    etapa de confirmação de identidade na urna / de cadastro do eleitor.
    """

    DURACAO_S = 1.5
    PASSO_MS = 30

    def __init__(self, master, ao_concluir=None, tamanho=96, fundo=None, textos=None):
        super().__init__(master, fg_color="transparent")
        self.ao_concluir = ao_concluir
        self.tam = tamanho
        self.fundo = fundo or tema.CARD
        self.textos = {"espera": "Segure aqui", "lendo": "Lendo…",
                       "ok": "Confirmada", "off": "Indisponível"}
        if textos:
            self.textos.update(textos)
        self.estado = "espera"
        self.ativo = True
        self._inicio = 0.0
        self._prog = 0.0
        self._job = None

        self.canvas = tk.Canvas(self, width=tamanho, height=tamanho, bg=self.fundo,
                                highlightthickness=0, cursor="hand2")
        self.canvas.pack()
        self.lbl = ctk.CTkLabel(self, text="", font=("Arial", 11, "bold"))
        self.lbl.pack(pady=(2, 0))

        self.canvas.bind("<ButtonPress-1>", self._pressionar)
        self.canvas.bind("<ButtonRelease-1>", self._soltar)
        self._desenhar()

    # ------------------------------------------------------------ API
    @property
    def confirmado(self):
        return self.estado == "ok"

    def resetar(self):
        self._cancelar()
        self.estado = "espera" if self.ativo else "off"
        self._prog = 0.0
        self._desenhar()

    def definir_ativo(self, ativo, texto_off=None):
        self.ativo = ativo
        if texto_off:
            self.textos["off"] = texto_off
        self.resetar()

    def marcar_confirmado(self):
        self._cancelar()
        self.estado, self._prog = "ok", 1.0
        self._desenhar()

    # ---------------------------------------------------------- eventos
    def _pressionar(self, _e=None):
        if not self.ativo or self.estado in ("ok", "lendo"):
            return
        self.estado = "lendo"
        self._inicio = time.monotonic()
        self._tick()

    def _soltar(self, _e=None):
        if self.estado == "lendo":
            self._cancelar()
            self.estado, self._prog = "espera", 0.0
            self._desenhar()

    def _tick(self):
        if self.estado != "lendo":
            return
        self._prog = min((time.monotonic() - self._inicio) / self.DURACAO_S, 1.0)
        if self._prog >= 1.0:
            self._job = None
            self.estado = "ok"
            self._desenhar()
            if self.ao_concluir:
                self.ao_concluir()
            return
        self._desenhar()
        self._job = self.after(self.PASSO_MS, self._tick)

    def _cancelar(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def destroy(self):
        self._cancelar()
        super().destroy()

    # ---------------------------------------------------------- desenho
    def _desenhar(self):
        c, t = self.canvas, self.tam
        c.delete("all")
        paleta = {
            "espera": (tema.AZUL_SUAVE, tema.AZUL_ESCURO),
            "lendo": (tema.AMARELO_CLARO, tema.AMARELO_ESCURO),
            "ok": (tema.VERDE_CLARO, tema.VERDE),
            "off": (tema.CINZA_SUAVE, "#A3A9B5"),
        }
        fundo_circ, cor = paleta[self.estado]
        m = 6
        c.create_oval(m, m, t - m, t - m, fill=fundo_circ, outline="")

        cx = cy = t / 2
        passo = t * 0.055
        for i in range(6):
            r = t * 0.11 + i * passo
            ini = (i * 47 + 20) % 360
            ext = 250 + (i % 3) * 30
            c.create_arc(cx - r, cy - r, cx + r, cy + r, start=ini, extent=ext,
                         style="arc", outline=cor, width=2)
        c.create_line(cx, cy - t * 0.05, cx, cy + t * 0.30, fill=cor, width=2)

        if self._prog > 0:
            a = 2
            c.create_arc(a, a, t - a, t - a, start=90, extent=-360 * self._prog,
                         style="arc", outline=tema.VERDE if self.estado == "ok"
                         else tema.AMARELO, width=4)
        cor_txt = {"espera": tema.AZUL_ESCURO, "lendo": tema.AMARELO_ESCURO,
                   "ok": tema.VERDE, "off": tema.TEXTO_SUAVE}[self.estado]
        self.lbl.configure(text=self.textos[self.estado], text_color=cor_txt)


class MenuMultiSelecao(ctk.CTkFrame):
    """Menu suspenso com seleção múltipla (caixas de marcação).

    opcoes: lista de (chave, texto). `selecionados()` devolve as chaves marcadas.
    O painel abre logo abaixo do botão e fecha em "Concluir", Esc, ao clicar
    de novo no botão ou ao clicar fora.
    """

    def __init__(self, master, titulo, opcoes=None, ao_mudar=None,
                 vazio="Nenhuma opção disponível."):
        super().__init__(master, fg_color="transparent")
        self.ao_mudar = ao_mudar
        self.vazio = vazio
        self._opcoes = []
        self._marcados = set()
        self._popup = None
        self._vars = {}

        ctk.CTkLabel(self, text=titulo, anchor="w", font=("Arial", 12, "bold"),
                     text_color=tema.AZUL_ESCURO).pack(fill="x", padx=2)
        self.botao = ctk.CTkButton(
            self, text="", anchor="w", height=34, corner_radius=8,
            border_width=1, border_color=tema.BORDA, fg_color="white",
            hover_color=tema.AZUL_SUAVE, text_color=tema.TEXTO,
            command=self.alternar)
        self.botao.pack(fill="x", pady=(2, 0))

        # fecha o painel ao clicar fora dele (o painel é outra janela, então
        # cliques dentro dele não chegam aqui)
        self.winfo_toplevel().bind("<Button-1>", self._clique_fora, add="+")
        self.definir_opcoes(opcoes or [])

    # ------------------------------------------------------------ dados
    def definir_opcoes(self, opcoes):
        self._opcoes = list(opcoes)
        chaves = {k for k, _ in self._opcoes}
        self._marcados &= chaves
        self._atualizar_botao()

    def selecionados(self):
        return [k for k, _ in self._opcoes if k in self._marcados]

    def limpar(self):
        self._marcados.clear()
        self._atualizar_botao()
        self._avisar()

    def _avisar(self):
        if self.ao_mudar:
            self.ao_mudar()

    def _atualizar_botao(self):
        n = len(self.selecionados())
        if not self._opcoes:
            texto, ativo = "Sem candidatos cadastrados", False
        elif n == 0:
            texto, ativo = "Selecionar candidatos", False
        elif n == 1:
            texto, ativo = "1 candidato selecionado", True
        else:
            texto, ativo = f"{n} candidatos selecionados", True
        self.botao.configure(
            text=f"{texto}   ▾",
            fg_color=tema.AZUL_SUAVE if ativo else "white",
            border_color=tema.AZUL if ativo else tema.BORDA)

    # ----------------------------------------------------------- painel
    def alternar(self):
        if self._popup is not None:
            self.fechar()
        else:
            self.abrir()

    def abrir(self):
        if self._popup is not None:
            return
        self.update_idletasks()
        n = max(len(self._opcoes), 1)
        altura_lista = min(n * 32 + 8, 220)
        altura = altura_lista + 92
        largura = max(self.botao.winfo_width(), 300)
        x = self.botao.winfo_rootx()
        y = self.botao.winfo_rooty() + self.botao.winfo_height() + 2
        if y + altura > self.winfo_screenheight():      # sem espaço: abre p/ cima
            y = self.botao.winfo_rooty() - altura - 2

        pop = ctk.CTkToplevel(self)
        pop.withdraw()
        pop.overrideredirect(True)
        pop.configure(fg_color=tema.BORDA)
        pop.geometry(f"{largura}x{altura}+{x}+{y}")
        self._popup = pop

        miolo = ctk.CTkFrame(pop, fg_color=tema.CARD, corner_radius=0)
        miolo.pack(fill="both", expand=True, padx=1, pady=1)

        if self._opcoes:
            barra = ctk.CTkFrame(miolo, fg_color="transparent")
            barra.pack(fill="x", padx=8, pady=(8, 2))
            ctk.CTkButton(barra, text="Marcar todos", width=100, height=26,
                          font=("Arial", 11), command=self._marcar_todos,
                          **tema.BOTAO_AMARELO).pack(side="left")
            ctk.CTkButton(barra, text="Limpar", width=70, height=26,
                          font=("Arial", 11), command=self._desmarcar_todos,
                          **tema.BOTAO_NEUTRO).pack(side="left", padx=6)

            lista = ctk.CTkScrollableFrame(miolo, fg_color="transparent",
                                           height=altura_lista)
            lista.pack(fill="both", expand=True, padx=4, pady=2)
            self._vars = {}
            for chave, texto in self._opcoes:
                var = ctk.BooleanVar(value=chave in self._marcados)
                self._vars[chave] = var
                ctk.CTkCheckBox(
                    lista, text=texto, variable=var, text_color=tema.TEXTO,
                    fg_color=tema.AZUL, hover_color=tema.AZUL_ESCURO,
                    border_color=tema.BORDA, checkbox_width=20, checkbox_height=20,
                    command=lambda k=chave: self._alterou(k)
                ).pack(fill="x", padx=6, pady=4)
        else:
            ctk.CTkLabel(miolo, text=self.vazio, wraplength=largura - 30,
                         text_color=tema.TEXTO_SUAVE, font=("Arial", 12)
                         ).pack(expand=True, pady=20)

        ctk.CTkButton(miolo, text="Concluir", height=30, command=self.fechar,
                      **tema.BOTAO).pack(fill="x", padx=8, pady=(2, 8))

        pop.bind("<Escape>", lambda _e: self.fechar())
        pop.transient(self.winfo_toplevel())
        pop.deiconify()
        pop.lift()
        pop.focus_force()

    def fechar(self):
        pop, self._popup = self._popup, None
        if pop is not None:
            try:
                pop.destroy()
            except tk.TclError:
                pass

    def _alterou(self, chave):
        if self._vars[chave].get():
            self._marcados.add(chave)
        else:
            self._marcados.discard(chave)
        self._atualizar_botao()
        self._avisar()

    def _marcar_todos(self):
        for chave, var in self._vars.items():
            var.set(True)
            self._marcados.add(chave)
        self._atualizar_botao()
        self._avisar()

    def _desmarcar_todos(self):
        for var in self._vars.values():
            var.set(False)
        self._marcados.clear()
        self._atualizar_botao()
        self._avisar()

    def _clique_fora(self, evento):
        if self._popup is None:
            return
        try:
            if not self.winfo_exists():
                return
            if str(evento.widget).startswith(str(self.botao)):
                return                       # o próprio botão trata o clique
        except tk.TclError:
            return
        self.fechar()

    def destroy(self):
        self.fechar()
        super().destroy()
