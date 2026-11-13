import os
from io import BytesIO

from PIL import Image, ImageDraw, ImageOps

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_FOTOS = os.path.join(RAIZ, "fotos")
AVATAR = os.path.join(RAIZ, "assets", "avatar.png")


def salvar_foto(origem, numero, prefixo="candidato"):
    with Image.open(origem) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((800, 800))
        os.makedirs(PASTA_FOTOS, exist_ok=True)
        nome = f"{prefixo}_{numero}.jpg"
        img.save(os.path.join(PASTA_FOTOS, nome), "JPEG", quality=90)
    return f"fotos/{nome}"


def remover_foto(caminho):
    """Apaga o arquivo de foto de um cadastro excluído (só dentro de fotos/)."""
    if not caminho:
        return
    absoluto = os.path.abspath(
        caminho if os.path.isabs(caminho) else os.path.join(RAIZ, caminho))
    if os.path.dirname(absoluto) == os.path.abspath(PASTA_FOTOS) and os.path.isfile(absoluto):
        try:
            os.remove(absoluto)
        except OSError:
            pass


def _resolver(caminho):
    if caminho:
        absoluto = caminho if os.path.isabs(caminho) else os.path.join(RAIZ, caminho)
        if os.path.exists(absoluto):
            return absoluto
    return AVATAR


def _recortar(caminho, tamanho_px, raio=0):
    """Abre a foto (ou o avatar), recorta no formato `tamanho_px` e,
    se `raio` > 0, arredonda os cantos (raio grande = foto redonda)."""
    with Image.open(_resolver(caminho)) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img = ImageOps.fit(img, tamanho_px, Image.LANCZOS, centering=(0.5, 0.3))
    if raio > 0:
        img = img.convert("RGBA")
        mascara = Image.new("L", tamanho_px, 0)
        ImageDraw.Draw(mascara).rounded_rectangle(
            (0, 0, tamanho_px[0] - 1, tamanho_px[1] - 1), radius=raio, fill=255)
        img.putalpha(mascara)
    return img


def carregar(caminho, tamanho, raio=0):
    """Imagem para as telas (CTkImage). `raio` em pixels da tela."""
    import customtkinter as ctk  # import tardio: o exportador não precisa da interface
    img = _recortar(caminho, (tamanho[0] * 2, tamanho[1] * 2), raio * 2)
    return ctk.CTkImage(light_image=img, dark_image=img, size=tamanho)


def foto_para_relatorio(caminho, tamanho_px):
    """Foto (ou avatar) em PNG dentro de um BytesIO, pronta para PDF/Excel."""
    img = _recortar(caminho, tamanho_px)
    buf = BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return buf
