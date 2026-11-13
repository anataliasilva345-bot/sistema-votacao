import customtkinter as ctk
from views import tema
from tkinter import filedialog, messagebox
from controllers.eleicao_controller import EleicaoController
from controllers.voto_controller import VotoController
from utils import imagens
from utils.exportador import exportar_resultado_xlsx, exportar_resultado_pdf


def _pct_txt(valor):
    return f"{valor:.1f}".replace(".", ",") + "%"


class TelaResultados(ctk.CTkFrame):
    FOTO = (52, 65)
    INTERVALO_MS = 3000   # atualização automática da apuração

    def __init__(self, master):
        super().__init__(master, fg_color=tema.FUNDO)
        self.eleicao_ctrl = EleicaoController()
        self.voto_ctrl = VotoController()
        self.dados_atuais = None
        self.eleicao_atual = None
        self._imgs = []      # referências das imagens exibidas
        self._cache = {}     # (foto) -> CTkImage

        ctk.CTkLabel(self, text="Apuração dos Resultados", anchor="w",
                     font=("Arial", 24, "bold"), text_color=tema.AZUL_LOGO
                     ).pack(fill="x", padx=24, pady=(20, 0))
        ctk.CTkLabel(self, text="Votos por candidato, brancos, nulos e relatórios",
                     anchor="w", font=("Arial", 12), text_color=tema.TEXTO_SUAVE
                     ).pack(fill="x", padx=24, pady=(0, 10))

        self.eleicoes = self.eleicao_ctrl.listar()

        topo = ctk.CTkFrame(self, **tema.CARD_MODERNO)
        topo.pack(pady=(0, 8), padx=24, fill="x")

        # Botões primeiro (lado direito): reservam o espaço deles antes do menu,
        # que tem texto longo e senão "espreme" os botões.
        ctk.CTkButton(topo, text="Exportar PDF", width=160, height=36,
                      font=("Arial", 13, "bold"),
                      command=self.exportar_pdf, **tema.BOTAO).pack(side="right", padx=(4, 12))
        ctk.CTkButton(topo, text="Exportar Excel", width=170, height=36,
                      font=("Arial", 13, "bold"),
                      command=self.exportar, **tema.BOTAO_AMARELO).pack(side="right", padx=4)
        ctk.CTkButton(topo, text="↻", width=44, height=36, command=self.apurar,
                      **tema.BOTAO_NEUTRO).pack(side="right", padx=4)

        self.sel = ctk.CTkOptionMenu(
            topo, **tema.OPTION,
            values=[e.descricao() for e in self.eleicoes] or ["(sem eleições)"],
            command=lambda _: self.apurar())
        # largura de pedido pequena: o texto longo da eleição não empurra os botões
        self.sel.configure(width=200, dynamic_resizing=False)
        self.sel.pack(side="left", fill="x", expand=True, padx=(12, 6), pady=12)

        self.resultado = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.resultado.pack(fill="both", expand=True, padx=(18, 12), pady=(0, 12))

        self._timer = None
        self._assin = None
        self.apurar()
        self._timer = self.after(self.INTERVALO_MS, self._auto_atualizar)

    # ------------------------------------------------- atualização automática
    def destroy(self):
        if self._timer:
            self.after_cancel(self._timer)
            self._timer = None
        super().destroy()

    def _assinatura(self):
        if not self.eleicao_atual:
            return None
        return (self.eleicao_atual.id,
                self.voto_ctrl.repo.total_votos(self.eleicao_atual.id))

    def _auto_atualizar(self):
        if not self.winfo_exists():
            return
        try:
            if self._assinatura() != self._assin:
                self.apurar()
        except Exception:
            pass  # banco ocupado: tenta no próximo ciclo
        self._timer = self.after(self.INTERVALO_MS, self._auto_atualizar)

    # ------------------------------------------------------------ helpers
    def _foto(self, caminho):
        chave = caminho or "__avatar__"
        if chave not in self._cache:
            self._cache[chave] = imagens.carregar(caminho, self.FOTO, raio=10)
        return self._cache[chave]

    def _vazio(self, texto):
        ctk.CTkLabel(self.resultado, text=texto, font=("Arial", 13),
                     text_color=tema.TEXTO_SUAVE).pack(pady=50)

    # ------------------------------------------------------------- apuração
    def apurar(self):
        for w in self.resultado.winfo_children():
            w.destroy()
        self._imgs.clear()

        desc = self.sel.get()
        self.eleicao_atual = next(
            (e for e in self.eleicoes if e.descricao() == desc), None)
        if not self.eleicao_atual:
            self.dados_atuais = None
            self._vazio("Nenhuma eleição disponível.")
            return
        self.dados_atuais = self.voto_ctrl.apurar(self.eleicao_atual)
        encerrada = self.eleicao_atual.status == "ENCERRADA"

        # Cabeçalho da eleição
        cab = ctk.CTkFrame(self.resultado, fg_color="transparent")
        cab.pack(fill="x", padx=6, pady=(4, 0))
        ctk.CTkLabel(cab, text=self.eleicao_atual.nome, font=("Arial", 18, "bold"),
                     text_color=tema.AZUL_ESCURO).pack(side="left")
        ctk.CTkLabel(cab, text="ENCERRADA" if encerrada else "ABERTA", height=24,
                     corner_radius=12, padx=10, font=("Arial", 11, "bold"),
                     fg_color=tema.VERMELHO_CLARO if encerrada else tema.VERDE_CLARO,
                     text_color=tema.VERMELHO if encerrada else tema.VERDE
                     ).pack(side="left", padx=10)

        for cargo, info in self.dados_atuais["por_cargo"].items():
            self._bloco_cargo(cargo, info, encerrada)
        self._assin = self._assinatura()

    def _bloco_cargo(self, cargo, info, encerrada):
        total, validos = info["total"], info["validos"]
        brancos, nulos = info["brancos"], info["nulos"]

        bloco = ctk.CTkFrame(self.resultado, **tema.CARD_MODERNO)
        bloco.pack(fill="x", padx=6, pady=10)

        # Faixa do cargo
        faixa = ctk.CTkFrame(bloco, corner_radius=10, fg_color=tema.AZUL_LOGO)
        faixa.pack(fill="x", padx=12, pady=(12, 8))
        ctk.CTkLabel(faixa, text=cargo.upper(), font=("Arial", 15, "bold"),
                     text_color="white").pack(side="left", padx=14, pady=8)
        ctk.CTkFrame(faixa, width=40, height=3, corner_radius=2,
                     fg_color=tema.AMARELO).pack(side="left")

        # KPIs
        kpis = ctk.CTkFrame(bloco, fg_color="transparent")
        kpis.pack(fill="x", padx=12)
        for i, (rotulo, valor) in enumerate((("Total de votos", total),
                                             ("Válidos", validos),
                                             ("Brancos", brancos),
                                             ("Nulos", nulos))):
            kpis.grid_columnconfigure(i, weight=1, uniform="k")
            k = ctk.CTkFrame(kpis, corner_radius=10, fg_color=tema.FUNDO)
            k.grid(row=0, column=i, padx=3, sticky="ew")
            ctk.CTkLabel(k, text=str(valor), font=("Arial", 18, "bold"),
                         text_color=tema.AZUL_ESCURO).pack(pady=(6, 0))
            ctk.CTkLabel(k, text=rotulo, font=("Arial", 10),
                         text_color=tema.TEXTO_SUAVE).pack(pady=(0, 6))

        ranking = info["ranking"]
        if not ranking:
            ctk.CTkLabel(bloco, text="Nenhum candidato cadastrado para este cargo.",
                         font=("Arial", 12, "italic"), text_color=tema.TEXTO_SUAVE
                         ).pack(pady=14)
        else:
            if validos == 0:
                ctk.CTkLabel(bloco, text="Nenhum voto válido ainda.",
                             font=("Arial", 12, "italic"),
                             text_color=tema.TEXTO_SUAVE
                             ).pack(anchor="w", padx=16, pady=(10, 0))
            maior = max(c.votos for c in ranking)
            empatados = sum(1 for c in ranking if c.votos == maior)
            for i, c in enumerate(ranking, start=1):
                lider = validos > 0 and c.votos == maior
                rotulo = None
                if lider:
                    rotulo = ("EMPATE" if empatados > 1
                              else "ELEITO" if encerrada else "LIDERANDO")
                self._linha_candidato(bloco, i, c, validos, lider, rotulo)

        # Brancos e nulos
        extra = ctk.CTkFrame(bloco, fg_color="transparent")
        extra.pack(fill="x", padx=12, pady=(4, 14))
        for i, (rotulo, qtd) in enumerate((("Votos em branco", brancos),
                                           ("Votos nulos", nulos))):
            extra.grid_columnconfigure(i, weight=1, uniform="e")
            pct = qtd / total * 100 if total else 0.0
            c = ctk.CTkFrame(extra, corner_radius=10, fg_color=tema.FUNDO)
            c.grid(row=0, column=i, padx=3, sticky="ew")
            topo = ctk.CTkFrame(c, fg_color="transparent")
            topo.pack(fill="x", padx=12, pady=(8, 2))
            ctk.CTkLabel(topo, text=rotulo, font=("Arial", 12, "bold"),
                         text_color=tema.TEXTO).pack(side="left")
            ctk.CTkLabel(topo, text=f"{qtd}  ({_pct_txt(pct)} do total)",
                         font=("Arial", 11), text_color=tema.TEXTO_SUAVE
                         ).pack(side="right")
            barra = ctk.CTkProgressBar(c, height=6, fg_color=tema.BORDA,
                                       progress_color=tema.TEXTO_SUAVE)
            barra.set(pct / 100)
            barra.pack(fill="x", padx=12, pady=(0, 10))

    def _linha_candidato(self, pai, pos, c, validos, lider, rotulo):
        pct = c.votos / validos * 100 if validos else 0.0

        linha = ctk.CTkFrame(
            pai, corner_radius=12,
            fg_color=tema.AMARELO_CLARO if lider else tema.CARD,
            border_width=2 if lider else 1,
            border_color=tema.AMARELO if lider else tema.BORDA)
        linha.pack(fill="x", padx=12, pady=5)

        ctk.CTkLabel(linha, text=f"{pos}º", width=36, font=("Arial", 16, "bold"),
                     text_color=tema.AMARELO_ESCURO if lider else tema.TEXTO_SUAVE
                     ).pack(side="left", padx=(10, 0))

        foto = self._foto(c.foto)
        self._imgs.append(foto)
        ctk.CTkLabel(linha, text="", image=foto).pack(side="left", padx=8, pady=8)

        info = ctk.CTkFrame(linha, fg_color="transparent", width=290, height=44)
        info.pack(side="left", padx=(4, 8))
        info.pack_propagate(False)  # largura fixa: barras de todas as linhas alinhadas
        nome = ctk.CTkFrame(info, fg_color="transparent")
        nome.pack(anchor="w")
        ctk.CTkLabel(nome, text=c.nome, font=("Arial", 14, "bold"),
                     text_color=tema.AZUL_LOGO).pack(side="left")
        if rotulo:
            ctk.CTkLabel(nome, text=rotulo, height=20, corner_radius=10, padx=8,
                         font=("Arial", 9, "bold"), fg_color=tema.AMARELO,
                         text_color=tema.TEXTO).pack(side="left", padx=8)
        ctk.CTkLabel(info, text=f"{c.partido}   •   Nº {c.numero}", anchor="w",
                     font=("Arial", 11), text_color=tema.TEXTO_SUAVE).pack(anchor="w")

        direita = ctk.CTkFrame(linha, fg_color="transparent")
        direita.pack(side="right", fill="x", expand=True, padx=(8, 16))
        topo = ctk.CTkFrame(direita, fg_color="transparent")
        topo.pack(fill="x")
        ctk.CTkLabel(topo, text=f"{c.votos} voto{'s' if c.votos != 1 else ''}",
                     font=("Arial", 16, "bold"), text_color=tema.TEXTO
                     ).pack(side="left")
        ctk.CTkLabel(topo, text=f"{_pct_txt(pct)} dos válidos", font=("Arial", 11),
                     text_color=tema.TEXTO_SUAVE).pack(side="right")
        barra = ctk.CTkProgressBar(direita, height=10, corner_radius=5,
                                   fg_color=tema.BORDA,
                                   progress_color=tema.AMARELO if lider else tema.AZUL)
        barra.set(pct / 100)
        barra.pack(fill="x", pady=(4, 0))

    # ----------------------------------------------------------- exportação
    def exportar(self):
        if not self.dados_atuais:
            messagebox.showwarning("Aviso", "Selecione uma eleição primeiro.")
            return
        caminho = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile=f"resultado_{self.eleicao_atual.nome.replace(' ', '_')}.xlsx")
        if not caminho:
            return
        try:
            exportar_resultado_xlsx(caminho, self.eleicao_atual, self.dados_atuais)
        except PermissionError:
            messagebox.showerror("Erro", "Feche o arquivo Excel se estiver aberto e tente novamente.")
            return
        messagebox.showinfo("Exportado", f"Resultado salvo em:\n{caminho}")

    def exportar_pdf(self):
        if not self.dados_atuais:
            messagebox.showwarning("Aviso", "Selecione uma eleição primeiro.")
            return
        caminho = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"resultado_{self.eleicao_atual.nome.replace(' ', '_')}.pdf")
        if not caminho:
            return
        try:
            exportar_resultado_pdf(caminho, self.eleicao_atual, self.dados_atuais)
        except PermissionError:
            messagebox.showerror("Erro", "Feche o arquivo PDF se estiver aberto e tente novamente.")
            return
        messagebox.showinfo("Exportado", f"Relatório salvo em:\n{caminho}")
