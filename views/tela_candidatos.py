import os
from tkinter import filedialog, messagebox

import customtkinter as ctk
from views import tema
from utils import imagens
from controllers.candidato_controller import CandidatoController
from models.cargos import CARGOS


class TelaCandidatos(ctk.CTkFrame):
    TEXTO_SEM_FOTO = "Sem foto (será usado o avatar em branco)"
    FOTO_FORM = (64, 80)
    FOTO_CARD = (62, 78)

    def __init__(self, master):
        super().__init__(master, fg_color=tema.FUNDO)
        self.ctrl = CandidatoController()
        self.foto_origem = None
        self.img_avatar = imagens.carregar(None, self.FOTO_FORM, raio=12)
        self._imgs = []  # mantém referência das imagens da lista

        ctk.CTkLabel(self, text="Cadastro de Candidatos", anchor="w",
                     font=("Arial", 24, "bold"), text_color=tema.AZUL_LOGO
                     ).pack(fill="x", padx=24, pady=(20, 0))
        ctk.CTkLabel(self, text="Cadastre candidatos e confira os já registrados",
                     anchor="w", font=("Arial", 12), text_color=tema.TEXTO_SUAVE
                     ).pack(fill="x", padx=24, pady=(0, 10))

        # ---------------------------------------------------- formulário
        form = ctk.CTkFrame(self, **tema.CARD_MODERNO)
        form.pack(padx=24, pady=(0, 6), fill="x")

        esquerda = ctk.CTkFrame(form, fg_color="transparent")
        esquerda.pack(side="left", padx=(18, 8), pady=14)
        self.preview = ctk.CTkLabel(esquerda, text="", image=self.img_avatar)
        self.preview.pack()

        campos = ctk.CTkFrame(form, fg_color="transparent")
        campos.pack(side="left", fill="x", expand=True, padx=(8, 18), pady=12)
        campos.grid_columnconfigure((0, 1, 2), weight=1)

        self.nome = ctk.CTkEntry(campos, placeholder_text="Nome do candidato", **tema.ENTRY)
        self.nome.grid(row=0, column=0, columnspan=3, padx=4, pady=4, sticky="ew")
        self.numero = ctk.CTkEntry(campos, placeholder_text="Número", **tema.ENTRY)
        self.numero.grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        self.partido = ctk.CTkEntry(campos, placeholder_text="Partido", **tema.ENTRY)
        self.partido.grid(row=1, column=1, padx=4, pady=4, sticky="ew")
        self.cargo = ctk.CTkOptionMenu(campos, **tema.OPTION, values=CARGOS)
        self.cargo.grid(row=1, column=2, padx=4, pady=4, sticky="ew")

        linha_foto = ctk.CTkFrame(campos, fg_color="transparent")
        linha_foto.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        ctk.CTkButton(linha_foto, text="📷  Escolher foto", width=140,
                      command=self._escolher_foto, **tema.BOTAO_AMARELO
                      ).pack(side="left", padx=4)
        ctk.CTkButton(linha_foto, text="Remover", width=80, command=self._limpar_foto,
                      **tema.BOTAO_NEUTRO).pack(side="left", padx=4)
        self.lbl_foto = ctk.CTkLabel(linha_foto, text=self.TEXTO_SEM_FOTO,
                                     font=("Arial", 11), text_color=tema.TEXTO_SUAVE)
        self.lbl_foto.pack(side="left", padx=8)
        ctk.CTkButton(linha_foto, text="Cadastrar", width=130, height=34,
                      command=self.salvar, **tema.BOTAO).pack(side="right", padx=4)

        self.msg = ctk.CTkLabel(self, text="", anchor="w", font=("Arial", 12))
        self.msg.pack(fill="x", padx=28)

        # ------------------------------------------------------- lista
        cab = ctk.CTkFrame(self, fg_color="transparent")
        cab.pack(fill="x", padx=24, pady=(4, 0))
        ctk.CTkLabel(cab, text="Candidatos cadastrados", font=("Arial", 15, "bold"),
                     text_color=tema.AZUL_ESCURO).pack(side="left")
        self.lbl_qtd = ctk.CTkLabel(cab, text="", font=("Arial", 12),
                                    text_color=tema.TEXTO_SUAVE)
        self.lbl_qtd.pack(side="left", padx=10)

        self.lista = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.lista.pack(fill="both", expand=True, padx=(18, 12), pady=(4, 12))
        self.lista.grid_columnconfigure((0, 1), weight=1, uniform="cand")

        self.carregar()

    # ------------------------------------------------------------- foto
    def _escolher_foto(self):
        caminho = filedialog.askopenfilename(
            title="Escolher foto do candidato",
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
            self.ctrl.cadastrar(self.nome.get(), self.numero.get(),
                                self.partido.get(), self.cargo.get(),
                                self.foto_origem)
            self.msg.configure(text="Candidato cadastrado!", text_color=tema.VERDE)
            for w in (self.nome, self.numero, self.partido):
                w.delete(0, "end")
            self._limpar_foto()
            self.carregar()
        except Exception as ex:
            self.msg.configure(text=f"Erro: {ex}", text_color=tema.VERMELHO)

    def _excluir(self, c):
        if not messagebox.askyesno(
                "Excluir candidato",
                f"Excluir o candidato {c.nome} (nº {c.numero})?\n\n"
                "Esta ação não pode ser desfeita.",
                icon="warning", parent=self.winfo_toplevel()):
            return
        try:
            self.ctrl.excluir(c.id)
            self.msg.configure(text=f"Candidato {c.nome} excluído.",
                               text_color=tema.AMARELO_ESCURO)
            self.after(200, self.carregar)  # espera o clique terminar
        except Exception as ex:
            self.msg.configure(text=f"Erro: {ex}", text_color=tema.VERMELHO)

    def carregar(self):
        for w in self.lista.winfo_children():
            w.destroy()
        self._imgs.clear()

        candidatos = sorted(self.ctrl.listar(), key=lambda c: (c.cargo, c.numero))
        self.lbl_qtd.configure(text=f"{len(candidatos)} no total")

        if not candidatos:
            ctk.CTkLabel(self.lista, text="Nenhum candidato cadastrado ainda.",
                         font=("Arial", 13), text_color=tema.TEXTO_SUAVE
                         ).grid(row=0, column=0, columnspan=2, pady=40)
            return

        for i, c in enumerate(candidatos):
            self._cartao(c).grid(row=i // 2, column=i % 2, padx=6, pady=6,
                                 sticky="nsew")

    def _cartao(self, c):
        cartao = ctk.CTkFrame(self.lista, **tema.CARD_MODERNO)

        foto = imagens.carregar(c.foto, self.FOTO_CARD, raio=12)
        self._imgs.append(foto)
        ctk.CTkLabel(cartao, text="", image=foto).pack(side="left", padx=(12, 12),
                                                       pady=12)

        info = ctk.CTkFrame(cartao, fg_color="transparent", height=78)
        info.pack(side="left", fill="x", expand=True, pady=12)
        ctk.CTkLabel(info, text=c.nome, anchor="w", justify="left", wraplength=170,
                     font=("Arial", 14, "bold"), text_color=tema.AZUL_LOGO
                     ).pack(fill="x")
        ctk.CTkLabel(info, text=c.cargo, anchor="w", font=("Arial", 11),
                     text_color=tema.TEXTO_SUAVE).pack(fill="x", pady=(0, 6))
        linha = ctk.CTkFrame(info, fg_color="transparent")
        linha.pack(fill="x")
        ctk.CTkLabel(linha, text=c.partido, height=24, corner_radius=12,
                     fg_color=tema.AZUL_SUAVE, text_color=tema.AZUL_ESCURO,
                     font=("Arial", 11, "bold"), padx=10).pack(side="left")
        ctk.CTkButton(linha, text="Excluir", width=64, height=24,
                      font=("Arial", 11, "bold"),
                      command=lambda c=c: self._excluir(c),
                      **tema.BOTAO_PERIGO).pack(side="right")

        caixa = ctk.CTkFrame(cartao, width=76, height=78, corner_radius=12,
                             fg_color=tema.AMARELO_CLARO)
        caixa.pack(side="right", padx=12, pady=12)
        caixa.pack_propagate(False)
        ctk.CTkLabel(caixa, text="Nº", font=("Arial", 10, "bold"),
                     text_color=tema.AMARELO_ESCURO).pack(pady=(10, 0))
        ctk.CTkLabel(caixa, text=str(c.numero), font=("Arial", 22, "bold"),
                     text_color=tema.TEXTO).pack()
        return cartao
