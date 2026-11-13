import os
import customtkinter as ctk
from PIL import Image

AZUL = "#596F99"
AZUL_ESCURO = "#3E5078"
AZUL_CLARO = "#C9D3E6"
AZUL_LOGO = "#022342"
AMARELO = "#FCC200"
AMARELO_HOVER = "#E0AB00"
AMARELO_ESCURO = "#9A7400"
VERDE = "#567371"
VERDE_HOVER = "#445E5C"
VERMELHO = "#B3261E"
VERMELHO_HOVER = "#8F1E18"
FUNDO = "#F2F4F8"
CARD = "#FFFFFF"
TEXTO = "#1F2937"
TEXTO_SUAVE = "#6B7280"
BORDA = "#D5DBE6"

# --- Paleta da barra lateral / cartões modernos ---
SIDEBAR = "#0B1F3A"
SIDEBAR_HOVER = "#16315A"
SIDEBAR_ATIVO = "#1D3F73"
SIDEBAR_TEXTO = "#B8C4DA"
VERDE_CLARO = "#E3EEEC"
AMARELO_CLARO = "#FFF4CC"
VERMELHO_CLARO = "#FBE9E7"
AZUL_SUAVE = "#E6EBF5"
CINZA_SUAVE = "#EEF0F4"

CAMINHO_LOGO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "logo_tse.png")

FRAME = dict(fg_color=CARD, border_width=1, border_color=BORDA, corner_radius=10)

ENTRY = dict(fg_color="white", border_color=BORDA, border_width=1,
             text_color=TEXTO, placeholder_text_color=TEXTO_SUAVE,
             corner_radius=8, height=34)

OPTION = dict(fg_color=AZUL, button_color=AZUL_ESCURO,
              button_hover_color=AZUL_ESCURO, text_color="white",
              dropdown_fg_color="white", dropdown_text_color=TEXTO,
              dropdown_hover_color=AZUL_CLARO, corner_radius=8, height=34)

TEXTBOX = dict(fg_color="white", text_color=TEXTO, border_width=1,
               border_color=BORDA, corner_radius=10)

BOTAO = dict(fg_color=AZUL, hover_color=AZUL_ESCURO, text_color="white",
             corner_radius=8)

BOTAO_AMARELO = dict(fg_color=AMARELO, hover_color=AMARELO_HOVER,
                     text_color=TEXTO, corner_radius=8)

BOTAO_VERDE = dict(fg_color=VERDE, hover_color=VERDE_HOVER,
                   text_color="white", corner_radius=8)

BOTAO_PERIGO = dict(fg_color=VERMELHO, hover_color=VERMELHO_HOVER,
                    text_color="white", corner_radius=8)

BOTAO_NEUTRO = dict(fg_color=TEXTO_SUAVE, hover_color="#4B5563",
                    text_color="white", corner_radius=8)

CARD_MODERNO = dict(fg_color=CARD, border_width=1, border_color=BORDA,
                    corner_radius=14)

TRANSP = dict(fg_color="transparent")

BOTAO_MENU = dict(fg_color="transparent", hover_color=AZUL, text_color="white",
                  anchor="w", corner_radius=8)


def configurar():
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")


def logo(largura):
    img = Image.open(CAMINHO_LOGO)
    altura = int(img.height * largura / img.width)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(largura, altura))


def faixa(master, altura=8):
    f = ctk.CTkFrame(master, height=altura, corner_radius=0, fg_color="transparent")
    f.grid_rowconfigure(0, weight=1)
    for i, cor in enumerate((AZUL, AMARELO, VERDE)):
        f.grid_columnconfigure(i, weight=1, uniform="faixa")
        ctk.CTkFrame(f, height=altura, width=1, corner_radius=0,
                     fg_color=cor).grid(row=0, column=i, sticky="nsew")
    return f


TECLA = dict(fg_color="#2B3A4B", hover_color="#18222D", text_color="white",
             corner_radius=6, font=("Arial", 22, "bold"), width=76, height=54)

TECLA_BRANCO = dict(fg_color="white", hover_color="#E5E7EB", text_color="#111827",
                    border_width=2, border_color="#9CA3AF", corner_radius=6,
                    font=("Arial", 13, "bold"), width=104, height=54)

TECLA_NULO = dict(fg_color="#D1D5DB", hover_color="#B9BFC9", text_color="#111827",
                  border_width=2, border_color="#9CA3AF", corner_radius=6,
                  font=("Arial", 13, "bold"), width=104, height=54)

TECLA_CORRIGE = dict(fg_color="#E8661B", hover_color="#C4540F", text_color="#111827",
                     corner_radius=6, font=("Arial", 13, "bold"),
                     width=104, height=54)

TECLA_CONFIRMA = dict(fg_color="#3DAA4A", hover_color="#2E8A3A", text_color="#111827",
                      corner_radius=6, font=("Arial", 14, "bold"),
                      width=104, height=54)
