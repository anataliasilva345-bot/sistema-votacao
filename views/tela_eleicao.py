import customtkinter as ctk
from views import tema
from views.componentes import MenuMultiSelecao
from controllers.eleicao_controller import EleicaoController
from controllers.candidato_controller import CandidatoController
from models.cargos import CARGOS


class TelaEleicao(ctk.CTkFrame):
    TXT_SELECIONE = "(selecione a eleição)"
    TXT_NENHUMA = "(nenhuma eleição aberta)"

    def __init__(self, master):
        super().__init__(master, fg_color=tema.FUNDO)
        self.ctrl = EleicaoController()
        self.cand_ctrl = CandidatoController()
        self.menus = {}          # cargo -> MenuMultiSelecao
        self.candidatos = {}     # id -> Candidato

        ctk.CTkLabel(self, text="Gestão de Eleições",
                     font=("Arial", 22, "bold"), text_color=tema.AZUL_ESCURO).pack(pady=10)

        # ✅ TUDO DENTRO DE UMA ÁREA COM SCROLL
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=0, pady=0)

        form = ctk.CTkFrame(self.scroll, **tema.FRAME)
        form.pack(pady=10, padx=20, fill="x")
        
        # Removemos as 3 colunas fixas e deixamos em coluna única
        form.grid_columnconfigure(0, weight=1)

        self.nome = ctk.CTkEntry(form, placeholder_text="Nome da eleição", **tema.ENTRY)
        self.nome.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        ctk.CTkLabel(form, text="Candidatos que participam da eleição "
                                "(escolha em cada cargo):",
                     font=("Arial", 12), text_color=tema.TEXTO_SUAVE, anchor="w"
                     ).grid(row=1, column=0, padx=10, pady=(4, 8), sticky="w")

        # ✅ UM MENU EMBAIXO DO OUTRO (evita sobreposição de 3 colunas)
        for i, cargo in enumerate(CARGOS):
            menu = MenuMultiSelecao(
                form, cargo, ao_mudar=self._atualizar_resumo,
                vazio=f"Nenhum candidato a {cargo} cadastrado.\n"
                      f"Cadastre na aba Candidatos.")
            menu.grid(row=2 + i, column=0, padx=8, pady=4, sticky="ew")
            self.menus[cargo] = menu

        self.lbl_resumo = ctk.CTkLabel(form, text="", anchor="w", justify="left",
                                       font=("Arial", 12))
        self.lbl_resumo.grid(row=100, column=0, padx=10, pady=(10, 10), sticky="w")
        
        ctk.CTkButton(form, text="Limpar seleção", command=self._limpar_selecao,
                      **tema.BOTAO_AMARELO).grid(row=101, column=0, padx=8, pady=(0, 12),
                                                 sticky="ew")

        ctk.CTkButton(self.scroll, text="Criar eleição", command=self.salvar, **tema.BOTAO).pack(pady=8)

        encerrar_box = ctk.CTkFrame(self.scroll, **tema.FRAME)
        encerrar_box.pack(pady=4, padx=20, fill="x")
        ctk.CTkLabel(encerrar_box, text="Encerrar eleição:").grid(
            row=0, column=0, padx=8, pady=8, sticky="w")
        self.sel_encerrar = ctk.CTkOptionMenu(
            encerrar_box, **tema.OPTION, values=[self.TXT_SELECIONE])
        self.sel_encerrar.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        ctk.CTkButton(encerrar_box, text="Encerrar eleição",
                      command=self.encerrar, **tema.BOTAO_PERIGO).grid(
            row=0, column=2, padx=8, pady=8)
        encerrar_box.grid_columnconfigure(1, weight=1)

        self.msg = ctk.CTkLabel(self.scroll, text="")
        self.msg.pack()

        self.lista = ctk.CTkTextbox(self.scroll, height=250, **tema.TEXTBOX)
        self.lista.pack(fill="both", expand=True, padx=20, pady=10)

        self.eleicoes = []
        self.abertas = {}  # rótulo exibido no menu -> Eleicao aberta
        self._carregar_candidatos()
        self._atualizar_resumo()
        self.carregar()

    # ------------------------------------------------------- candidatos
    @staticmethod
    def _rotulo(c):
        return f"{c.numero} - {c.nome} ({c.partido})"

    def _carregar_candidatos(self):
        todos = self.cand_ctrl.listar()
        self.candidatos = {c.id: c for c in todos}
        for cargo, menu in self.menus.items():
            do_cargo = sorted((c for c in todos if c.cargo == cargo),
                              key=lambda c: c.numero)
            menu.definir_opcoes([(c.id, self._rotulo(c)) for c in do_cargo])

    def _ids_selecionados(self):
        ids = []
        for menu in self.menus.values():
            ids.extend(menu.selecionados())
        return ids

    def _atualizar_resumo(self):
        partes = [f"{cargo}: {len(m.selecionados())}"
                  for cargo, m in self.menus.items() if m.selecionados()]
        if partes:
            self.lbl_resumo.configure(
                text="Selecionados  →  " + "   •   ".join(partes))
        else:
            self.lbl_resumo.configure(text="Nenhum candidato selecionado.")

    def _limpar_selecao(self):
        for menu in self.menus.values():
            menu.fechar()
            menu.limpar()
        self._atualizar_resumo()

    # ------------------------------------------------------------ ações
    def salvar(self):
        try:
            self.ctrl.cadastrar(self.nome.get(), self._ids_selecionados())
            self.msg.configure(text="Eleição criada!", text_color=tema.VERDE)
            self.nome.delete(0, "end")
            self._limpar_selecao()
            self.carregar()
        except Exception as ex:
            self.msg.configure(text=f"Erro: {ex}", text_color=tema.VERMELHO)

    def encerrar(self):
        eleicao = self.abertas.get(self.sel_encerrar.get())
        if not eleicao:
            self.msg.configure(text="Selecione uma eleição aberta para encerrar.",
                               text_color=tema.VERMELHO)
            return
        try:
            self.ctrl.encerrar(eleicao.id)
            self.msg.configure(text=f"Eleição '{eleicao.nome}' encerrada.",
                               text_color=tema.AMARELO_ESCURO)
            self.carregar()
        except Exception as ex:
            self.msg.configure(text=f"Erro: {ex}", text_color=tema.VERMELHO)

    def _atualizar_menu_encerrar(self):
        """Preenche o menu suspenso com o nome das eleições ainda abertas."""
        abertas = [e for e in self.eleicoes if e.esta_aberta]
        nomes = [e.nome for e in abertas]
        self.abertas = {}
        for e in abertas:
            # nomes repetidos ganham o id para não ficarem ambíguos
            rotulo = e.nome if nomes.count(e.nome) == 1 else f"{e.nome} (#{e.id})"
            self.abertas[rotulo] = e
        if self.abertas:
            self.sel_encerrar.configure(values=list(self.abertas))
            self.sel_encerrar.set(self.TXT_SELECIONE)
        else:
            self.sel_encerrar.configure(values=[self.TXT_NENHUMA])
            self.sel_encerrar.set(self.TXT_NENHUMA)

    def carregar(self):
        self.eleicoes = self.ctrl.listar()
        self.lista.delete("1.0", "end")
        for el in self.eleicoes:
            self.lista.insert("end", el.descricao() + "\n")
            for cargo in el.cargos:
                nomes = [f"{c.numero} {c.nome}"
                         for c in (self.candidatos.get(i) for i in el.candidatos_ids)
                         if c and c.cargo == cargo]
                if nomes:
                    self.lista.insert("end", f"     • {cargo}: {'; '.join(nomes)}\n")
            self.lista.insert("end", "\n")
        self._atualizar_menu_encerrar()