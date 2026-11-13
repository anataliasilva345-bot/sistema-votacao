import os
from tkinter import filedialog, messagebox

import customtkinter as ctk
from views import tema
from views.componentes import BotaoBiometria
from utils import imagens
from controllers.eleitor_controller import EleitorController


class TelaEleitores(ctk.CTkFrame):
    TEXTO_SEM_FOTO = "Sem foto (será usado o avatar em branco)"
    FOTO_FORM = (64, 80)
    FOTO_CARD = (56, 70)

    def __init__(self, master):
        super().__init__(master, fg_color=tema.FUNDO)
        self.ctrl = EleitorController()
        self.foto_origem = None
        self.img_avatar = imagens.carregar(None, self.FOTO_FORM, raio=12)
        self._imgs = []

        ctk.CTkLabel(self, text="Cadastro de Eleitores", anchor="w",
                     font=("Arial", 24, "bold"), text_color=tema.AZUL_LOGO
                     ).pack(fill="x", padx=24, pady=(20, 0))
        ctk.CTkLabel(self, text="Cadastre o eleitor com foto e biometria para a identificação na urna",
                     anchor="w", font=("Arial", 12), text_color=tema.TEXTO_SUAVE
                     ).pack(fill="x", padx=24, pady=(0, 10))

        # ---------------------------------------------------- formulário
        form = ctk.CTkFrame(self, **tema.CARD_MODERNO)
        form.pack(padx=24, pady=(0, 6), fill="x")

        esquerda = ctk.CTkFrame(form, fg_color="transparent")
        esquerda.pack(side="left", padx=(18, 8), pady=14)
        self.preview = ctk.CTkLabel(esquerda, text="", image=self.img_avatar)
        self.preview.pack()

        direita = ctk.CTkFrame(form, fg_color="transparent")
        direita.pack(side="right", padx=(8, 18), pady=10)
        self.bio = BotaoBiometria(
            direita, tamanho=84,
            textos={"espera": "Segure p/ cadastrar", "ok": "Cadastrada"})
        self.bio.pack()

        campos = ctk.CTkFrame(form, fg_color="transparent")
        campos.pack(side="left", fill="x", expand=True, padx=8, pady=12)
        campos.grid_columnconfigure((0, 1), weight=1)

        self.nome = ctk.CTkEntry(campos, placeholder_text="Nome completo", **tema.ENTRY)
        self.nome.grid(row=0, column=0, columnspan=2, padx=4, pady=4, sticky="ew")
        self.cpf = ctk.CTkEntry(campos, placeholder_text="CPF (somente números)", **tema.ENTRY)
        self.cpf.grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        self.titulo = ctk.CTkEntry(campos, placeholder_text="Título de eleitor", **tema.ENTRY)
        self.titulo.grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        linha = ctk.CTkFrame(campos, fg_color="transparent")
        linha.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        ctk.CTkButton(linha, text="📷  Escolher foto", width=140,
                      command=self._escolher_foto, **tema.BOTAO_AMARELO
                      ).pack(side="left", padx=4)
        ctk.CTkButton(linha, text="Remover", width=80, command=self._limpar_foto,
                      **tema.BOTAO_NEUTRO).pack(side="left", padx=4)
        self.lbl_foto = ctk.CTkLabel(linha, text=self.TEXTO_SEM_FOTO,
                                     font=("Arial", 11), text_color=tema.TEXTO_SUAVE)
        self.lbl_foto.pack(side="left", padx=8)
        ctk.CTkButton(linha, text="Cadastrar", width=120, height=34,
                      command=self.salvar, **tema.BOTAO).pack(side="right", padx=4)

        self.msg = ctk.CTkLabel(self, text="", anchor="w", font=("Arial", 12))
        self.msg.pack(fill="x", padx=28)

        # ------------------------------------------------------- lista
        cab = ctk.CTkFrame(self, fg_color="transparent")
        cab.pack(fill="x", padx=24, pady=(4, 0))
        ctk.CTkLabel(cab, text="Eleitores cadastrados", font=("Arial", 15, "bold"),
                     text_color=tema.AZUL_ESCURO).pack(side="left")
        self.lbl_qtd = ctk.CTkLabel(cab, text="", font=("Arial", 12),
                                    text_color=tema.TEXTO_SUAVE)
        self.lbl_qtd.pack(side="left", padx=10)

        self.lista = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lista.pack(fill="both", expand=True, padx=(18, 12), pady=(4, 12))
        self.lista.grid_columnconfigure((0, 1), weight=1, uniform="eleitor")

        self.carregar()

    # ------------------------------------------------------------- foto
    def _escolher_foto(self):
        caminho = filedialog.askopenfilename(
            title="Escolher foto do eleitor",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"),
                       ("Todos os arquivos", "*.*")])
        if not caminho:
            return
        try:
            miniatura = imagens.carregar(caminho, self.FOTO_FORM, raio=12)
        except Exception:
            self.msg.configure(text="Erro: arquivo de imagem inválido.",
                               text_color=tema.VERMELHO)
            return
        self.foto_origem = caminho
        self.preview.configure(image=miniatura)
        self.lbl_foto.configure(text=os.path.basename(caminho))

    def _limpar_foto(self):
        self.foto_origem = None
        self.preview.configure(image=self.img_avatar)
        self.lbl_foto.configure(text=self.TEXTO_SEM_FOTO)

    # ------------------------------------------------------------ ações
    def salvar(self):
        try:
            self.ctrl.cadastrar(self.nome.get(), self.cpf.get(), self.titulo.get(),
                                self.foto_origem, self.bio.confirmado)
            self.msg.configure(text="Eleitor cadastrado!", text_color=tema.VERDE)
            for w in (self.nome, self.cpf, self.titulo):
                w.delete(0, "end")
            self._limpar_foto()
            self.bio.resetar()
            self.carregar()
        except Exception as ex:
            self.msg.configure(text=f"Erro: {ex}", text_color=tema.VERMELHO)

    def _excluir(self, e):
        if not messagebox.askyesno(
                "Excluir eleitor",
                f"Excluir o eleitor {e.nome} (título {e.titulo})?\n\n"
                "Esta ação não pode ser desfeita.",
                icon="warning", parent=self.winfo_toplevel()):
            return
        try:
            self.ctrl.excluir(e.id)
            self.msg.configure(text=f"Eleitor {e.nome} excluído.",
                               text_color=tema.AMARELO_ESCURO)
            self.after(200, self.carregar)  # espera o clique terminar
        except Exception as ex:
            self.msg.configure(text=f"Erro: {ex}", text_color=tema.VERMELHO)

    def carregar(self):
        for w in self.lista.winfo_children():
            w.destroy()
        self._imgs.clear()

        eleitores = self.ctrl.listar()
        self.lbl_qtd.configure(text=f"{len(eleitores)} no total")
        if not eleitores:
            ctk.CTkLabel(self.lista, text="Nenhum eleitor cadastrado ainda.",
                         font=("Arial", 13), text_color=tema.TEXTO_SUAVE
                         ).grid(row=0, column=0, columnspan=2, pady=40)
            return
        for i, e in enumerate(eleitores):
            self._cartao(e).grid(row=i // 2, column=i % 2, padx=6, pady=6,
                                 sticky="nsew")

    def _etiqueta(self, pai, texto, cor, fundo):
        return ctk.CTkLabel(pai, text=texto, height=22, corner_radius=11, padx=8,
                            font=("Arial", 10, "bold"), text_color=cor, fg_color=fundo)

    def _cartao(self, e):
        cartao = ctk.CTkFrame(self.lista, **tema.CARD_MODERNO)
        foto = imagens.carregar(e.foto, self.FOTO_CARD, raio=12)
        self._imgs.append(foto)
        ctk.CTkLabel(cartao, text="", image=foto).pack(side="left", padx=12, pady=12)

        info = ctk.CTkFrame(cartao, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True, pady=12, padx=(0, 12))
        ctk.CTkLabel(info, text=e.nome, anchor="w", justify="left", wraplength=230,
                     font=("Arial", 14, "bold"), text_color=tema.AZUL_LOGO
                     ).pack(fill="x")
        ctk.CTkLabel(info, text=f"Título: {e.titulo}   •   CPF: {e.cpf}", anchor="w",
                     font=("Arial", 11), text_color=tema.TEXTO_SUAVE
                     ).pack(fill="x", pady=(0, 6))
        tags = ctk.CTkFrame(info, fg_color="transparent")
        tags.pack(fill="x")
        ctk.CTkButton(tags, text="Excluir", width=64, height=24,
                      font=("Arial", 11, "bold"),
                      command=lambda e=e: self._excluir(e),
                      **tema.BOTAO_PERIGO).pack(side="right")
        if e.biometria:
            self._etiqueta(tags, "✔ Biometria", tema.VERDE, tema.VERDE_CLARO
                           ).pack(side="left", padx=(0, 6))
        else:
            self._etiqueta(tags, "Sem biometria", tema.TEXTO_SUAVE, tema.CINZA_SUAVE
                           ).pack(side="left", padx=(0, 6))
        if e.ja_votou:
            self._etiqueta(tags, "Já votou", tema.AMARELO_ESCURO, tema.AMARELO_CLARO
                           ).pack(side="left")
        return cartao
