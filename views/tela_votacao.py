from datetime import datetime

import customtkinter as ctk
from views import tema
from views.componentes import BotaoBiometria
from utils import imagens
from controllers.eleicao_controller import EleicaoController
from controllers.voto_controller import VotoController
from rede import cliente_rede

FOTO_TAM = (130, 160)
FOTO_ELEITOR = (64, 80)


class TelaVotacao(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=tema.FUNDO)
        if cliente_rede.conectado():   # urna em rede: tudo passa pelo servidor
            self.eleicao_ctrl = cliente_rede.EleicaoControllerRede()
            self.voto_ctrl = cliente_rede.VotoControllerRede()
        else:                          # modo local (app admin atual)
            self.eleicao_ctrl = EleicaoController()
            self.voto_ctrl = VotoController()
        self.especial = None  # None, "BRANCO" ou "NULO" (teclas BRANCO/NULO)
        self.fim = None
        self.job_fim = None
        self.img_avatar = imagens.carregar(None, FOTO_TAM)
        self.img_atual = self.img_avatar
        self.img_eleitor_avatar = imagens.carregar(None, FOTO_ELEITOR, raio=10)
        self.img_eleitor = self.img_eleitor_avatar
        self.eleitor = None
        self._titulo_ident = None

        ctk.CTkLabel(self, text="Urna Eletrônica",
                     font=("Arial", 24, "bold"),
                     text_color=tema.AZUL_ESCURO).pack(pady=(10, 6))

        self.eleicoes = [e for e in self.eleicao_ctrl.listar() if e.esta_aberta]

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(pady=6, padx=30, fill="x")

        # O card do eleitor é empacotado ANTES do formulário: assim ele reserva
        # o espaço dele primeiro e o formulário ocupa só o que sobrar.
        ident = ctk.CTkFrame(topo, **tema.CARD_MODERNO)
        ident.pack(side="right", fill="y", padx=(12, 0), pady=0)

        frame = ctk.CTkFrame(topo, **tema.FRAME)
        frame.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(frame, text="Eleição:").grid(row=0, column=0, padx=6, pady=5)
        self.sel_eleicao = ctk.CTkOptionMenu(
            frame, **tema.OPTION,
            values=[e.descricao() for e in self.eleicoes] or ["(nenhuma aberta)"],
            command=self._atualizar_cargos)
        self.sel_eleicao.grid(row=0, column=1, padx=6, pady=5, sticky="ew")

        ctk.CTkLabel(frame, text="Cargo:").grid(row=1, column=0, padx=6, pady=5)
        self.sel_cargo = ctk.CTkOptionMenu(
            frame, **tema.OPTION, values=["(selecione)"],
            command=lambda _c: self._atualizar_preview())
        self.sel_cargo.grid(row=1, column=1, padx=6, pady=5, sticky="ew")

        ctk.CTkLabel(frame, text="Título do eleitor:").grid(row=2, column=0, padx=6, pady=5)
        self.titulo = ctk.CTkEntry(frame, placeholder_text="Título", **tema.ENTRY)
        self.titulo.grid(row=2, column=1, padx=6, pady=5, sticky="ew")
        self.titulo.bind("<KeyRelease>", self._atualizar_eleitor)

        frame.grid_columnconfigure(1, weight=1)
        # largura de pedido pequena: o texto longo da eleição não "empurra" o card
        for m in (self.sel_eleicao, self.sel_cargo):
            m.configure(width=200, dynamic_resizing=False)

        # ---- Identificação do eleitor: foto + biometria (simulada)
        # ✅ Ajustado para grid: garante que o sensor apareça embaixo da foto
        # Foto do eleitor (Coluna 0, Linha 0)
        self.lbl_foto_eleitor = ctk.CTkLabel(ident, text="", image=self.img_eleitor)
        self.lbl_foto_eleitor.grid(row=0, column=0, rowspan=2, padx=(12, 8), pady=(10, 5))

        # Nome e Instrução (Coluna 1, Linha 0)
        dados = ctk.CTkFrame(ident, fg_color="transparent")
        dados.grid(row=0, column=1, sticky="nw", padx=(0, 12), pady=(12, 0))
        
        self.lbl_eleitor_nome = ctk.CTkLabel(
            dados, text="Identificação", anchor="w", justify="left", wraplength=200,
            font=("Arial", 13, "bold"), text_color=tema.AZUL_LOGO)
        self.lbl_eleitor_nome.pack(fill="x")
        self.lbl_eleitor_info = ctk.CTkLabel(
            dados, text="Digite o título do eleitor", anchor="w", justify="left",
            wraplength=200, font=("Arial", 11), text_color=tema.TEXTO_SUAVE)
        self.lbl_eleitor_info.pack(fill="x", pady=(2, 0))

        # Biometria (Coluna 1, Linha 1) - Fica embaixo do nome, com espaço garantido
        self.bio = BotaoBiometria(ident, tamanho=64, ao_concluir=self._bio_ok)
        self.bio.grid(row=1, column=1, sticky="nw", padx=(0, 12), pady=(5, 12))
        self.bio.definir_ativo(False, "Aguardando")

        urna = ctk.CTkFrame(self, **tema.TRANSP)
        urna.pack(pady=6, padx=30, fill="x")
        urna.grid_columnconfigure(0, weight=1)

        tela = ctk.CTkFrame(urna, fg_color="white", border_width=3,
                            border_color="#1F2937", corner_radius=8)
        tela.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        tela.grid_columnconfigure(1, weight=1)

        self.lbl_foto = ctk.CTkLabel(tela, text="", image=self.img_avatar)
        self.lbl_foto.grid(row=0, column=0, rowspan=5, padx=14, pady=14, sticky="n")

        self.lbl_cargo_tela = ctk.CTkLabel(
            tela, text="SEU VOTO PARA", font=("Arial", 12, "bold"),
            text_color=tema.TEXTO_SUAVE, anchor="w")
        self.lbl_cargo_tela.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=(14, 0))

        caixa_numero = ctk.CTkFrame(tela, fg_color="transparent")
        caixa_numero.grid(row=1, column=1, sticky="w", pady=(4, 6))
        ctk.CTkLabel(caixa_numero, text="Número:", font=("Arial", 14, "bold"),
                     text_color=tema.TEXTO).pack(side="left", padx=(0, 10))
        self.numero = ctk.CTkEntry(
            caixa_numero, width=170, justify="center",
            font=("Arial", 30, "bold"), **{**tema.ENTRY, "height": 56})
        self.numero.pack(side="left")
        self.numero.bind("<KeyRelease>", self._atualizar_preview)

        self.lbl_nome = ctk.CTkLabel(
            tela, text="", font=("Arial", 18, "bold"), text_color=tema.TEXTO,
            anchor="w", justify="left", wraplength=320)
        self.lbl_nome.grid(row=2, column=1, sticky="ew", padx=(0, 14))

        self.lbl_partido = ctk.CTkLabel(
            tela, text="", font=("Arial", 15), text_color=tema.TEXTO,
            anchor="w", justify="left")
        self.lbl_partido.grid(row=3, column=1, sticky="ew", padx=(0, 14))

        self.lbl_status = ctk.CTkLabel(
            tela, text="", font=("Arial", 13, "bold"), text_color=tema.TEXTO,
            anchor="w", justify="left", wraplength=320)
        self.lbl_status.grid(row=4, column=1, sticky="ew", padx=(0, 14), pady=(6, 0))

        ctk.CTkLabel(
            tela, text="Verde: CONFIRMA   •   Laranja: CORRIGE   •   Branco: em branco   •   Cinza: NULO",
            font=("Arial", 11), text_color=tema.TEXTO_SUAVE).grid(
                row=5, column=0, columnspan=2, pady=(0, 10))

        teclado = ctk.CTkFrame(urna, fg_color="#E4E7EC", border_width=1,
                               border_color=tema.BORDA, corner_radius=12)
        teclado.grid(row=0, column=1, sticky="n")

        disposicao = [("1", 0, 0), ("2", 0, 1), ("3", 0, 2),
                      ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
                      ("7", 2, 0), ("8", 2, 1), ("9", 2, 2),
                      ("0", 3, 1)]
        for digito, linha, coluna in disposicao:
            ctk.CTkButton(teclado, text=digito,
                          command=lambda d=digito: self._digitar(d),
                          **tema.TECLA).grid(row=linha, column=coluna, padx=5, pady=5)

        ctk.CTkButton(teclado, text="BRANCO", command=self._tecla_branco,
                      **tema.TECLA_BRANCO).grid(row=0, column=3, padx=5, pady=5)
        ctk.CTkButton(teclado, text="NULO", command=self._tecla_nulo,
                      **tema.TECLA_NULO).grid(row=1, column=3, padx=5, pady=5)
        ctk.CTkButton(teclado, text="CORRIGE", command=self._corrigir,
                      **tema.TECLA_CORRIGE).grid(row=2, column=3, padx=5, pady=5)
        ctk.CTkButton(teclado, text="CONFIRMA", command=self._confirmar,
                      **tema.TECLA_CONFIRMA).grid(row=3, column=3, padx=5, pady=5)

        self.msg = ctk.CTkLabel(self, text="", font=("Arial", 14))
        self.msg.pack(pady=8)

        if self.eleicoes:
            self._atualizar_cargos(self.eleicoes[0].descricao())
        self._atualizar_preview()

    # ------------------------------------------------ identificação
    def _atualizar_eleitor(self, _evento=None):
        titulo = self.titulo.get().strip()
        eleitor = self.voto_ctrl.buscar_eleitor(titulo) if titulo else None
        mudou = titulo != self._titulo_ident
        self._titulo_ident = titulo
        self.eleitor = eleitor

        if not titulo:
            self._mostrar_eleitor(None, "Identificação", "Digite o título do eleitor",
                                  tema.TEXTO_SUAVE)
            self.bio.definir_ativo(False, "Aguardando")
        elif not eleitor:
            self._mostrar_eleitor(None, "Eleitor não encontrado",
                                  "Confira o número do título.", tema.VERMELHO)
            self.bio.definir_ativo(False, "Aguardando")
        elif eleitor.biometria:
            self._mostrar_eleitor(eleitor.foto, eleitor.nome,
                                  "Segure o leitor para confirmar a biometria.",
                                  tema.AMARELO_ESCURO)
            if mudou:
                self.bio.definir_ativo(True)
        else:
            self._mostrar_eleitor(eleitor.foto, eleitor.nome,
                                  "Sem biometria — liberado pelo título.",
                                  tema.TEXTO_SUAVE)
            self.bio.definir_ativo(False, "Sem digital")

    def _mostrar_eleitor(self, caminho_foto, nome, info, cor):
        self.img_eleitor = (imagens.carregar(caminho_foto, FOTO_ELEITOR, raio=10)
                            if caminho_foto else self.img_eleitor_avatar)
        self.lbl_foto_eleitor.configure(image=self.img_eleitor)
        self.lbl_eleitor_nome.configure(text=nome)
        self.lbl_eleitor_info.configure(text=info, text_color=cor)

    def _bio_ok(self):
        if self.eleitor:
            self.lbl_eleitor_info.configure(text="Identidade confirmada. Pode votar.",
                                            text_color=tema.VERDE)

    def _checar_identificacao(self):
        if not self.titulo.get().strip():
            raise ValueError("Informe o título do eleitor.")
        self._atualizar_eleitor()
        if not self.eleitor:
            raise ValueError("Eleitor não encontrado.")
        if self.eleitor.biometria and not self.bio.confirmado:
            raise ValueError("Confirme a biometria do eleitor antes de votar.")

    def destroy(self):
        if self.job_fim:
            self.after_cancel(self.job_fim)
            self.job_fim = None
        super().destroy()

    def _digitar(self, digito):
        if len(self.numero.get()) >= 5:
            return
        self.numero.insert("end", digito)
        self._atualizar_preview()

    def _tecla_branco(self):
        self.numero.delete(0, "end")
        self.especial = "BRANCO"
        self._atualizar_preview()

    def _tecla_nulo(self):
        self.numero.delete(0, "end")
        self.especial = "NULO"
        self._atualizar_preview()

    def _corrigir(self):
        self.numero.delete(0, "end")
        self.especial = None
        self.msg.configure(text="")
        self._atualizar_preview()

    def _confirmar(self):
        if self.especial == "BRANCO":
            self.votar_branco()
        elif self.especial == "NULO":
            self.votar_nulo()
        else:
            self.votar_valido()

    def _mostrar(self, imagem, nome, partido, status, cor_status):
        self.img_atual = imagem
        self.lbl_foto.configure(image=imagem)
        self.lbl_nome.configure(text=nome)
        self.lbl_partido.configure(text=partido)
        self.lbl_status.configure(text=status, text_color=cor_status)

    def _atualizar_preview(self, _evento=None):
        cargo = self.sel_cargo.get()
        if cargo and cargo != "(selecione)":
            self.lbl_cargo_tela.configure(text=f"SEU VOTO PARA: {cargo.upper()}")
        else:
            self.lbl_cargo_tela.configure(text="SEU VOTO PARA")

        texto = self.numero.get().strip()
        if texto:
            self.especial = None

        if self.especial == "BRANCO":
            self._mostrar(self.img_avatar, "VOTO EM BRANCO", "",
                          "Aperte CONFIRMA para confirmar.", tema.TEXTO)
            return
        if self.especial == "NULO":
            self._mostrar(self.img_avatar, "VOTO NULO", "",
                          "Aperte CONFIRMA para confirmar.", tema.VERMELHO)
            return
        if not texto:
            self._mostrar(self.img_avatar, "", "", "", tema.TEXTO)
            return

        candidato = self.voto_ctrl.buscar_candidato(texto, cargo)
        eleicao = next((e for e in self.eleicoes
                        if e.descricao() == self.sel_eleicao.get()), None)
        if (candidato and eleicao and candidato.cargo == cargo
                and not eleicao.aceita_candidato(candidato.id)):
            candidato = None  # não participa desta eleição
        if not candidato:
            self._mostrar(self.img_avatar, "NÚMERO ERRADO", "",
                          "VOTO NULO — aperte CONFIRMA para confirmar.", tema.VERMELHO)
            return

        foto = imagens.carregar(candidato.foto, FOTO_TAM)
        if candidato.cargo != cargo:
            self._mostrar(foto, f"Nome: {candidato.nome}",
                          f"Partido: {candidato.partido}",
                          f"Este candidato concorre a {candidato.cargo}, "
                          f"não a este cargo.", tema.VERMELHO)
        else:
            self._mostrar(foto, f"Nome: {candidato.nome}",
                          f"Partido: {candidato.partido}",
                          "Aperte CONFIRMA para confirmar.", tema.VERDE)

    def _mostrar_fim(self):
        if self.fim is not None:
            return  # Evita abrir duas telas de "FIM" se clicar 2x rápido
        self.fim = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        self.fim.place(relx=0, rely=0, relwidth=1, relheight=1)
        ctk.CTkLabel(self.fim, text=datetime.now().strftime("%d/%m/%Y   %H:%M:%S"),
                     font=("Arial", 13), text_color=tema.TEXTO_SUAVE).place(x=20, y=14)
        ctk.CTkLabel(self.fim, text="FIM", font=("Arial", 150, "bold"),
                     text_color="#111827").place(relx=0.5, rely=0.45, anchor="center")
        ctk.CTkLabel(self.fim, text="VOTOU", font=("Arial", 20, "bold"),
                     text_color=tema.TEXTO_SUAVE).place(relx=0.96, rely=0.95, anchor="se")
        self.fim.focus_set()
        self.job_fim = self.after(3000, self._fechar_fim)

    def _fechar_fim(self):
        self.job_fim = None
        if self.fim is not None:
            self.fim.destroy()
            self.fim = None

    def _atualizar_cargos(self, descricao):
        eleicao = next((e for e in self.eleicoes if e.descricao() == descricao), None)
        if eleicao:
            self.sel_cargo.configure(values=eleicao.cargos)
            if eleicao.cargos:
                self.sel_cargo.set(eleicao.cargos[0])
        else:
            self.sel_cargo.configure(values=["(selecione)"])
            self.sel_cargo.set("(selecione)")
        self._atualizar_preview()

    def _get_eleicao(self):
        eleicao = next((e for e in self.eleicoes
                        if e.descricao() == self.sel_eleicao.get()), None)
        if not eleicao:
            raise ValueError("Selecione uma eleição aberta.")
        return eleicao

    def _get_cargo(self, eleicao):
        cargo = self.sel_cargo.get()
        if cargo not in eleicao.cargos:
            raise ValueError("Selecione um cargo válido.")
        return cargo

    def votar_valido(self):
        try:
            eleicao = self._get_eleicao()
            cargo = self._get_cargo(eleicao)
            self._checar_identificacao()
            self.voto_ctrl.registrar_voto(
                eleicao, cargo, self.titulo.get().strip(),
                self.numero.get().strip(), tipo="VALIDO")
            self.msg.configure(text="✔ Voto registrado com sucesso!",
                               text_color=tema.VERDE)
            self.titulo.delete(0, "end")
            self._atualizar_eleitor()
            self.numero.delete(0, "end")
            self._atualizar_preview()
            self._mostrar_fim()
        except Exception as ex:
            self.msg.configure(text=f"✖ {ex}", text_color=tema.VERMELHO)

    def votar_branco(self):
        try:
            eleicao = self._get_eleicao()
            cargo = self._get_cargo(eleicao)
            self._checar_identificacao()
            self.voto_ctrl.registrar_voto(
                eleicao, cargo, self.titulo.get().strip(),
                numero_candidato=None, tipo="BRANCO")
            self.msg.configure(text="✔ Voto em branco registrado!",
                               text_color=tema.VERDE)
            self.titulo.delete(0, "end")
            self._atualizar_eleitor()
            self.numero.delete(0, "end")
            self.especial = None
            self._atualizar_preview()
            self._mostrar_fim()
        except Exception as ex:
            self.msg.configure(text=f"✖ {ex}", text_color=tema.VERMELHO)

    def votar_nulo(self):
        try:
            eleicao = self._get_eleicao()
            cargo = self._get_cargo(eleicao)
            self._checar_identificacao()
            self.voto_ctrl.registrar_voto(
                eleicao, cargo, self.titulo.get().strip(),
                numero_candidato=None, tipo="NULO")
            self.msg.configure(text="✔ Voto nulo registrado!",
                               text_color=tema.VERDE)
            self.titulo.delete(0, "end")
            self._atualizar_eleitor()
            self.numero.delete(0, "end")
            self.especial = None
            self._atualizar_preview()
            self._mostrar_fim()
        except Exception as ex:
            self.msg.configure(text=f"✖ {ex}", text_color=tema.VERMELHO)