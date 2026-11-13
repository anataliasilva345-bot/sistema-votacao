import csv
import os
from datetime import datetime

from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, OneCellAnchor
from openpyxl.drawing.xdr import XDRPositiveSize2D
from openpyxl.utils.units import pixels_to_EMU
from openpyxl.formatting.rule import DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image,
                                KeepTogether, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle)

AZUL = colors.HexColor("#596F99")
AZUL_ESCURO = colors.HexColor("#3E5078")
AMARELO = colors.HexColor("#FCC200")
AMARELO_CLARO = colors.HexColor("#FFF4CC")
VERDE = colors.HexColor("#567371")
CINZA = colors.HexColor("#6B7280")
CINZA_CLARO = colors.HexColor("#F2F4F8")
BORDA = colors.HexColor("#D5DBE6")
TEXTO = colors.HexColor("#1F2937")

from utils.imagens import foto_para_relatorio

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(RAIZ, "assets", "logo_tse.png")


FOTO_PDF = (8.8 * mm, 11 * mm)     # proporção 4:5
LARGURA_BARRA_PDF = 27 * mm        # cabe na coluna "Proporção" (34 mm - margens)


ALTURA_LINHA_FOTO = 52            # pontos
FOTO_XL_PX = (50, 62)             # largura x altura em pixels (4:5)


def _pct(parte, total):
    return (parte / total * 100) if total else 0.0


def _fmt_pct(valor):
    return f"{valor:.1f}".replace(".", ",") + "%"


def _fmt_int(valor):
    return f"{valor:,}".replace(",", ".")


def _agora():
    return datetime.now().strftime("%d/%m/%Y às %H:%M")


def _resumo_cargo(info):
    validos = sum(c.votos for c in info["ranking"])
    return {
        "validos": validos,
        "brancos": info["brancos"],
        "nulos": info["nulos"],
        "total": info["total"],
    }


def exportar_resultado_csv(caminho: str, nome_eleicao: str, dados: dict):
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        w.writerow(["RELATÓRIO DE APURAÇÃO"])
        w.writerow(["Eleição", nome_eleicao])
        w.writerow(["Emitido em", _agora()])
        w.writerow([])

        w.writerow(["RESUMO POR CARGO"])
        w.writerow(["Cargo", "Total de votos", "Votos válidos",
                    "Brancos", "Nulos", "% Brancos", "% Nulos"])
        for cargo, info in dados["por_cargo"].items():
            r = _resumo_cargo(info)
            w.writerow([cargo, r["total"], r["validos"], r["brancos"],
                        r["nulos"], _fmt_pct(_pct(r["brancos"], r["total"])),
                        _fmt_pct(_pct(r["nulos"], r["total"]))])
        w.writerow([])

        w.writerow(["RESULTADO POR CANDIDATO"])
        w.writerow(["Cargo", "Posição", "Número", "Candidato", "Partido",
                    "Votos", "% dos válidos"])
        for cargo, info in dados["por_cargo"].items():
            validos = sum(c.votos for c in info["ranking"])
            for i, c in enumerate(info["ranking"], 1):
                w.writerow([cargo, f"{i}º", c.numero, c.nome, c.partido,
                            c.votos, _fmt_pct(_pct(c.votos, validos))])
            total = info["total"]
            w.writerow([cargo, "-", "-", "Votos em branco", "-", info["brancos"],
                        _fmt_pct(_pct(info["brancos"], total)) + " do total"])
            w.writerow([cargo, "-", "-", "Votos nulos", "-", info["nulos"],
                        _fmt_pct(_pct(info["nulos"], total)) + " do total"])


def _barra(percentual, largura=38 * mm, altura=4 * mm, cor=AZUL):
    d = Drawing(largura, altura)
    d.add(Rect(0, 0, largura, altura, fillColor=CINZA_CLARO,
               strokeColor=BORDA, strokeWidth=0.4))
    cheio = largura * min(max(percentual, 0), 100) / 100
    if cheio > 0:
        d.add(Rect(0, 0, cheio, altura, fillColor=cor, strokeColor=None))
    return d


def _estilos():
    base = dict(fontName="Helvetica", textColor=TEXTO, leading=12)
    return {
        "titulo": ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=20,
                                 textColor=AZUL_ESCURO, leading=22),
        "sub": ParagraphStyle("sub", fontSize=10, textColor=CINZA, leading=14,
                              fontName="Helvetica"),
        "cargo": ParagraphStyle("cargo", fontName="Helvetica-Bold", fontSize=12,
                                textColor=colors.white, leading=15),
        "secao": ParagraphStyle("secao", fontName="Helvetica-Bold", fontSize=13,
                                textColor=AZUL_ESCURO, leading=15, spaceAfter=2),
        "normal": ParagraphStyle("normal", fontSize=9.5, **base),
        "cel": ParagraphStyle("cel", fontSize=9.5, **base),
        "cel_b": ParagraphStyle("cel_b", fontSize=9.5,
                                **{**base, "fontName": "Helvetica-Bold"}),
        "cab": ParagraphStyle("cab", fontName="Helvetica-Bold", fontSize=8.5,
                              textColor=colors.white, leading=11),
        "cab_c": ParagraphStyle("cab_c", fontName="Helvetica-Bold", fontSize=8.5,
                                textColor=colors.white, leading=11,
                                alignment=TA_CENTER),
        "kpi_n": ParagraphStyle("kpi_n", fontName="Helvetica-Bold", fontSize=15,
                                textColor=AZUL_ESCURO, leading=17,
                                alignment=TA_CENTER),
        "kpi_t": ParagraphStyle("kpi_t", fontName="Helvetica", fontSize=8,
                                textColor=CINZA, leading=10,
                                alignment=TA_CENTER),
        "vazio": ParagraphStyle("vazio", fontName="Helvetica-Oblique",
                                fontSize=9.5, textColor=CINZA, leading=13),
    }


def _rodape(canvas, doc):
    largura, altura = A4
    canvas.saveState()
    terco = largura / 3
    for i, cor in enumerate((AZUL, AMARELO, VERDE)):
        canvas.setFillColor(cor)
        canvas.rect(i * terco, 0, terco, 4 * mm, stroke=0, fill=1)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(CINZA)
    canvas.drawString(18 * mm, 9 * mm, "Sistema de Votação Eletrônica")
    canvas.drawRightString(largura - 18 * mm, 9 * mm, f"Página {doc.page}")
    canvas.restoreState()


def _cabecalho(est, nome, status, largura_util):
    logo = Image(LOGO, width=42 * mm, height=42 * mm * 510 / 1072)
    bloco = [
        Paragraph("Relatório de Apuração", est["titulo"]),
        Spacer(1, 1 * mm),
        Paragraph(f"<b>Eleição:</b> {nome}", est["sub"]),
        Paragraph(f"<b>Situação:</b> {status}", est["sub"]),
        Paragraph(f"<b>Emitido em:</b> {_agora()}", est["sub"]),
    ]
    t = Table([[bloco, logo]], colWidths=[largura_util - 48 * mm, 48 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, AMARELO),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
    ]))
    return t


def _quadro_resumo(est, dados, largura_util):
    linhas = [[Paragraph(h, est["cab"]) for h in
               ("Cargo", "Total", "Válidos", "Brancos", "Nulos")]]
    for h in linhas[0][1:]:
        h.style = est["cab_c"]
    for cargo, info in dados["por_cargo"].items():
        r = _resumo_cargo(info)
        linhas.append([
            Paragraph(cargo, est["cel_b"]),
            *[Paragraph(_fmt_int(v), ParagraphStyle(
                "n", parent=est["cel"], alignment=TA_CENTER))
              for v in (r["total"], r["validos"], r["brancos"], r["nulos"])],
        ])
    resto = largura_util - 55 * mm
    t = Table(linhas, colWidths=[55 * mm] + [resto / 4] * 4, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _tabela_brancos_nulos(est, r, largura_util):
    """Linhas de votos em branco e nulos (percentual sobre o total de votos)."""
    centro = ParagraphStyle("cbn", parent=est["cel"], alignment=TA_CENTER)
    linhas = [[Paragraph("Votos não atribuídos a candidatos", est["cab"]),
               Paragraph("Votos", est["cab_c"]),
               Paragraph("% do total", est["cab_c"])]]
    for rotulo, qtd in (("Votos em branco", r["brancos"]),
                        ("Votos nulos", r["nulos"])):
        linhas.append([Paragraph(rotulo, est["cel_b"]),
                       Paragraph(_fmt_int(qtd), centro),
                       Paragraph(_fmt_pct(_pct(qtd, r["total"])), centro)])
    t = Table(linhas, colWidths=[largura_util - 42 * mm, 20 * mm, 22 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CINZA),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def _bloco_cargo(est, cargo, info, encerrada, largura_util):
    r = _resumo_cargo(info)

    faixa = Table([[Paragraph(cargo.upper(), est["cargo"])]],
                  colWidths=[largura_util])
    faixa.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), AZUL),
        ("LINEBELOW", (0, 0), (-1, -1), 2, AMARELO),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    kpis = [[
        [Paragraph(_fmt_int(r["total"]), est["kpi_n"]), Paragraph("TOTAL DE VOTOS", est["kpi_t"])],
        [Paragraph(_fmt_int(r["validos"]), est["kpi_n"]), Paragraph("VÁLIDOS", est["kpi_t"])],
        [Paragraph(_fmt_int(r["brancos"]), est["kpi_n"]), Paragraph("BRANCOS", est["kpi_t"])],
        [Paragraph(_fmt_int(r["nulos"]), est["kpi_n"]), Paragraph("NULOS", est["kpi_t"])],
    ]]
    quadro = Table(kpis, colWidths=[largura_util / 4] * 4)
    quadro.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, BORDA),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDA),
        ("BACKGROUND", (0, 0), (-1, -1), CINZA_CLARO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    partes = [faixa, quadro, Spacer(1, 2 * mm)]

    if r["validos"] == 0:
        partes.append(Paragraph("Nenhum voto válido registrado para este cargo.",
                                est["vazio"]))
        if r["brancos"] or r["nulos"]:
            partes.append(Spacer(1, 2 * mm))
            partes.append(_tabela_brancos_nulos(est, r, largura_util))
        partes.append(Spacer(1, 4 * mm))
        return [CondPageBreak(40 * mm), KeepTogether(partes)]

    cabecalho = [Paragraph("Pos.", est["cab_c"]), Paragraph("Foto", est["cab_c"]),
                 Paragraph("Nº", est["cab_c"]),
                 Paragraph("Candidato", est["cab"]), Paragraph("Partido", est["cab"]),
                 Paragraph("Votos", est["cab_c"]), Paragraph("%", est["cab_c"]),
                 Paragraph("Proporção", est["cab"])]
    linhas = [cabecalho]
    maior = max(c.votos for c in info["ranking"])
    empatados = sum(1 for c in info["ranking"] if c.votos == maior)
    destaque = []
    centro = ParagraphStyle("c", parent=est["cel"], alignment=TA_CENTER)
    centro_b = ParagraphStyle("cb", parent=est["cel_b"], alignment=TA_CENTER)
    for i, c in enumerate(info["ranking"], 1):
        lider = c.votos == maior and maior > 0
        pct = _pct(c.votos, r["validos"])
        nome = c.nome
        if lider:
            if empatados > 1:
                rotulo = "EMPATE"
            else:
                rotulo = "ELEITO" if encerrada else "LIDERANDO"
            nome += f"  <font size=7 color='#3E5078'><b>{rotulo}</b></font>"
            destaque.append(len(linhas))
        linhas.append([
            Paragraph(f"{i}º", centro_b if lider else centro),
            Image(foto_para_relatorio(c.foto, (176, 220)),
                  width=FOTO_PDF[0], height=FOTO_PDF[1]),
            Paragraph(str(c.numero), centro),
            Paragraph(nome, est["cel_b"] if lider else est["cel"]),
            Paragraph(c.partido, est["cel"]),
            Paragraph(_fmt_int(c.votos), centro_b if lider else centro),
            Paragraph(_fmt_pct(pct), centro_b if lider else centro),
            _barra(pct, largura=LARGURA_BARRA_PDF, cor=AMARELO if lider else AZUL),
        ])

    # Pos., Foto, Nº, Candidato (resto), Partido, Votos, %, Proporção
    larguras = [13 * mm, 17 * mm, 11 * mm, 0, 19 * mm, 16 * mm, 18 * mm, 34 * mm]
    larguras[3] = largura_util - sum(larguras)
    tabela = Table(linhas, colWidths=larguras, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_ESCURO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CINZA_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for idx in destaque:
        estilo.append(("BACKGROUND", (0, idx), (-1, idx), AMARELO_CLARO))
    tabela.setStyle(TableStyle(estilo))

    # A tabela de candidatos pode quebrar entre páginas (cabeçalho repetido);
    # só o fechamento (brancos/nulos + nota) fica junto. O CondPageBreak evita
    # deixar a faixa do cargo sozinha no fim da página.
    fechamento = KeepTogether([
        Spacer(1, 2 * mm),
        _tabela_brancos_nulos(est, r, largura_util),
        Spacer(1, 1.5 * mm),
        Paragraph("Percentuais dos candidatos calculados sobre os votos válidos; "
                  "brancos e nulos, sobre o total de votos.", est["vazio"]),
        Spacer(1, 5 * mm),
    ])
    return [CondPageBreak(60 * mm)] + partes + [tabela, fechamento]


def exportar_resultado_pdf(caminho: str, eleicao, dados: dict):
    est = _estilos()
    largura, altura = A4
    margem = 18 * mm
    util = largura - 2 * margem

    doc = BaseDocTemplate(
        caminho, pagesize=A4,
        leftMargin=margem, rightMargin=margem,
        topMargin=15 * mm, bottomMargin=18 * mm,
        title=f"Relatório de Apuração - {eleicao.nome}",
        author="Sistema de Votação Eletrônica")
    moldura = Frame(margem, 18 * mm, util, altura - 33 * mm, id="corpo",
                    leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="p", frames=[moldura], onPage=_rodape)])

    encerrada = eleicao.status == "ENCERRADA"
    historia = [
        _cabecalho(est, eleicao.nome, eleicao.status.capitalize(), util),
        Spacer(1, 4 * mm),
        Paragraph("Resumo geral", est["secao"]),
        _quadro_resumo(est, dados, util),
        Spacer(1, 5 * mm),
        CondPageBreak(70 * mm),
        Paragraph("Resultado por cargo", est["secao"]),
        Spacer(1, 1 * mm),
    ]
    for cargo, info in dados["por_cargo"].items():
        historia.extend(_bloco_cargo(est, cargo, info, encerrada, util))

    doc.build(historia)


def exportar_resultado_xlsx(caminho: str, eleicao, dados: dict):
    wb = Workbook()
    ws = wb.active
    ws.title = "Apuração"
    ws.sheet_view.showGridLines = False

    for col, larg in zip("ABCDEFGH", (12, 7, 9, 32, 14, 11, 14, 26)):
        ws.column_dimensions[col].width = larg

    c_azul, c_escuro, c_amarelo = "596F99", "3E5078", "FCC200"
    c_verde, c_claro, c_borda = "567371", "F2F4F8", "D5DBE6"
    c_destaque, c_texto, c_cinza = "FFF4CC", "1F2937", "6B7280"

    def fonte(tam=10, negrito=False, cor=c_texto, italico=False):
        return Font(name="Arial", size=tam, bold=negrito, color=cor, italic=italico)

    def fundo(cor):
        return PatternFill("solid", start_color=cor, end_color=cor)

    lado = Side(style="thin", color=c_borda)
    borda = Border(left=lado, right=lado, top=lado, bottom=lado)
    amarelo_lado = Side(style="medium", color=c_amarelo)

    def mesclar(linha, c1, c2):
        if c1 != c2:
            ws.merge_cells(start_row=linha, start_column=c1,
                           end_row=linha, end_column=c2)

    def celula(linha, coluna, valor, fnt=None, fill=None, alin="left",
               fmt=None, com_borda=True):
        c = ws.cell(row=linha, column=coluna, value=valor)
        c.font = fnt or fonte()
        c.alignment = Alignment(horizontal=alin, vertical="center",
                                wrap_text=False, indent=1 if alin == "left" else 0)
        if fill:
            c.fill = fundo(fill)
        if fmt:
            c.number_format = fmt
        if com_borda:
            c.border = borda
        return c

    def faixa_mesclada(linha, c1, c2, valor, fnt, fill, alin="left", altura=None):
        for col in range(c1, c2 + 1):
            ws.cell(row=linha, column=col).fill = fundo(fill)
            ws.cell(row=linha, column=col).border = borda
        celula(linha, c1, valor, fnt, fill, alin)
        mesclar(linha, c1, c2)
        if altura:
            ws.row_dimensions[linha].height = altura

    def bloco_brancos_nulos(linha, r, com_nota=True):
        """Tabela de votos em branco e nulos; devolve a próxima linha livre."""
        ws.row_dimensions[linha].height = 22
        faixa_mesclada(linha, 1, 5, "Votos não atribuídos a candidatos",
                       fonte(10, True, "FFFFFF"), c_cinza, "left")
        celula(linha, 6, "Votos", fonte(10, True, "FFFFFF"), c_cinza, "center")
        celula(linha, 7, "% do total", fonte(10, True, "FFFFFF"), c_cinza, "center")
        celula(linha, 8, "Proporção", fonte(10, True, "FFFFFF"), c_cinza, "left")
        linha += 1
        for i, (rotulo, qtd) in enumerate((("Votos em branco", r["brancos"]),
                                           ("Votos nulos", r["nulos"]))):
            cor = "FFFFFF" if i % 2 == 0 else c_claro
            pct = _pct(qtd, r["total"]) / 100
            ws.row_dimensions[linha].height = 22
            faixa_mesclada(linha, 1, 5, rotulo, fonte(10, True), cor, "left")
            celula(linha, 6, qtd, fonte(10), cor, "center", "#,##0")
            celula(linha, 7, pct, fonte(10), cor, "center", "0.0%")
            celula(linha, 8, pct, fonte(10), cor, "center", ";;;")
            ws.conditional_formatting.add(
                f"H{linha}",
                DataBarRule(start_type="num", start_value=0,
                            end_type="num", end_value=1,
                            color=c_cinza, showValue=False))
            linha += 1
        if com_nota:
            n = ws.cell(row=linha, column=1,
                        value="Percentuais dos candidatos calculados sobre os votos "
                              "válidos; brancos e nulos, sobre o total de votos.")
            n.font = fonte(8, False, c_cinza, True)
            n.alignment = Alignment(horizontal="left", vertical="center", indent=1)
            mesclar(linha, 1, 8)
            linha += 1
        return linha

    fotos_xl = []   # mantém os buffers vivos até o wb.save()
    larg_col_px = int(12 * 7 + 5)

    def colocar_foto(linha, caminho):
        """Insere a foto do candidato centralizada na coluna A da linha."""
        buf = foto_para_relatorio(caminho, (FOTO_XL_PX[0] * 3, FOTO_XL_PX[1] * 3))
        fotos_xl.append(buf)
        img = XLImage(buf)
        img.width, img.height = FOTO_XL_PX
        altura_px = ALTURA_LINHA_FOTO * 4 / 3
        marcador = AnchorMarker(
            col=0, row=linha - 1,
            colOff=pixels_to_EMU(max((larg_col_px - FOTO_XL_PX[0]) // 2, 0)),
            rowOff=pixels_to_EMU(max(int((altura_px - FOTO_XL_PX[1]) // 2), 0)))
        img.anchor = OneCellAnchor(
            _from=marcador,
            ext=XDRPositiveSize2D(pixels_to_EMU(FOTO_XL_PX[0]),
                                  pixels_to_EMU(FOTO_XL_PX[1])))
        ws.add_image(img)

    ws.row_dimensions[1].height = 34
    for r in (2, 3, 4):
        ws.row_dimensions[r].height = 18

    t = ws.cell(row=1, column=1, value="Relatório de Apuração")
    t.font = fonte(20, True, c_escuro)
    t.alignment = Alignment(horizontal="left", vertical="center")
    mesclar(1, 1, 6)

    info = [("Eleição:", eleicao.nome),
            ("Situação:", eleicao.status.capitalize()),
            ("Emitido em:", _agora())]
    for i, (rotulo, valor) in enumerate(info, start=2):
        a = ws.cell(row=i, column=1, value=rotulo)
        a.font = fonte(10, True, c_cinza)
        a.alignment = Alignment(horizontal="left", vertical="center")
        b = ws.cell(row=i, column=2, value=valor)
        b.font = fonte(10, False, c_texto)
        b.alignment = Alignment(horizontal="left", vertical="center")
        mesclar(i, 2, 5)

    for col in range(1, 9):
        ws.cell(row=4, column=col).border = Border(bottom=amarelo_lado)

    if os.path.exists(LOGO):
        img = XLImage(LOGO)
        img.width, img.height = 175, int(175 * 510 / 1072)
        ws.add_image(img, "G1")

    linha = 6
    c = ws.cell(row=linha, column=1, value="Resumo geral")
    c.font = fonte(13, True, c_escuro)
    ws.row_dimensions[linha].height = 22
    linha += 1

    faixa_mesclada(linha, 1, 4, "Cargo", fonte(10, True, "FFFFFF"), c_escuro, "left", 22)
    for col, rotulo in zip((5, 6, 7, 8), ("Total", "Válidos", "Brancos", "Nulos")):
        celula(linha, col, rotulo, fonte(10, True, "FFFFFF"), c_escuro, "center")
    linha += 1

    for i, (cargo, info_cargo) in enumerate(dados["por_cargo"].items()):
        r = _resumo_cargo(info_cargo)
        cor = "FFFFFF" if i % 2 == 0 else c_claro
        ws.row_dimensions[linha].height = 20
        faixa_mesclada(linha, 1, 4, cargo, fonte(10, True), cor, "left")
        for col, v in zip((5, 6, 7, 8),
                          (r["total"], r["validos"], r["brancos"], r["nulos"])):
            celula(linha, col, v, fonte(), cor, "center", "#,##0")
        linha += 1

    linha += 1
    c = ws.cell(row=linha, column=1, value="Resultado por cargo")
    c.font = fonte(13, True, c_escuro)
    ws.row_dimensions[linha].height = 22
    linha += 2

    encerrada = eleicao.status == "ENCERRADA"

    for cargo, info_cargo in dados["por_cargo"].items():
        r = _resumo_cargo(info_cargo)

        faixa_mesclada(linha, 1, 8, cargo.upper(),
                       fonte(12, True, "FFFFFF"), c_azul, "left", 24)
        for col in range(1, 9):
            ws.cell(row=linha, column=col).border = Border(
                left=lado if col == 1 else None,
                right=lado if col == 8 else None,
                bottom=amarelo_lado)
        linha += 1

        grupos = [(1, 2, "TOTAL DE VOTOS", r["total"]),
                  (3, 4, "VÁLIDOS", r["validos"]),
                  (5, 6, "BRANCOS", r["brancos"]),
                  (7, 8, "NULOS", r["nulos"])]
        for c1, c2, rotulo, valor in grupos:
            for col in range(c1, c2 + 1):
                for rr in (linha, linha + 1):
                    ws.cell(row=rr, column=col).fill = fundo(c_claro)
                    ws.cell(row=rr, column=col).border = borda
            celula(linha, c1, valor, fonte(16, True, c_escuro), c_claro,
                   "center", "#,##0")
            celula(linha + 1, c1, rotulo, fonte(8, False, c_cinza), c_claro, "center")
            mesclar(linha, c1, c2)
            mesclar(linha + 1, c1, c2)
        ws.row_dimensions[linha].height = 28
        ws.row_dimensions[linha + 1].height = 16
        linha += 3

        if r["validos"] == 0:
            c = ws.cell(row=linha, column=1,
                        value="Nenhum voto válido registrado para este cargo.")
            c.font = fonte(10, False, c_cinza, True)
            c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
            mesclar(linha, 1, 8)
            ws.row_dimensions[linha].height = 20
            linha += 2
            if r["brancos"] or r["nulos"]:
                linha = bloco_brancos_nulos(linha, r, com_nota=False)
            linha += 2
            continue

        ws.row_dimensions[linha].height = 22
        for col, rotulo, alin in ((1, "Foto", "center"), (2, "Pos.", "center"),
                                  (3, "Nº", "center"),
                                  (4, "Candidato", "left"), (5, "Partido", "left"),
                                  (6, "Votos", "center"), (7, "% dos válidos", "center"),
                                  (8, "Proporção", "left")):
            celula(linha, col, rotulo, fonte(10, True, "FFFFFF"), c_escuro, alin)
        linha += 1

        maior = max(c.votos for c in info_cargo["ranking"])
        empatados = sum(1 for c in info_cargo["ranking"] if c.votos == maior)

        for i, cand in enumerate(info_cargo["ranking"], 1):
            lider = cand.votos == maior and maior > 0
            pct = _pct(cand.votos, r["validos"]) / 100
            if lider:
                cor = c_destaque
                if empatados > 1:
                    rotulo = "EMPATE"
                else:
                    rotulo = "ELEITO" if encerrada else "LIDERANDO"
                nome = f"{cand.nome}  ({rotulo})"
            else:
                cor = "FFFFFF" if i % 2 == 1 else c_claro
                nome = cand.nome
            ws.row_dimensions[linha].height = ALTURA_LINHA_FOTO
            celula(linha, 1, None, fonte(10), cor, "center")
            colocar_foto(linha, cand.foto)
            celula(linha, 2, f"{i}º", fonte(10, lider), cor, "center")
            celula(linha, 3, cand.numero, fonte(10), cor, "center")
            celula(linha, 4, nome, fonte(10, lider), cor, "left")
            celula(linha, 5, cand.partido, fonte(10), cor, "left")
            celula(linha, 6, cand.votos, fonte(10, lider), cor, "center", "#,##0")
            celula(linha, 7, pct, fonte(10, lider), cor, "center", "0.0%")
            celula(linha, 8, pct, fonte(10), cor, "center", ";;;")
            ws.conditional_formatting.add(
                f"H{linha}",
                DataBarRule(start_type="num", start_value=0,
                            end_type="num", end_value=1,
                            color=c_amarelo if lider else c_azul,
                            showValue=False))
            linha += 1
        linha += 1
        linha = bloco_brancos_nulos(linha, r)
        linha += 2

    ws.row_dimensions[linha].height = 6
    for c1, c2, cor in ((1, 3, c_azul), (4, 6, c_amarelo), (7, 8, c_verde)):
        for col in range(c1, c2 + 1):
            ws.cell(row=linha, column=col).fill = fundo(cor)
    linha += 1
    c = ws.cell(row=linha, column=1, value="Sistema de Votação Eletrônica")
    c.font = fonte(8, False, c_cinza)

    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f"A1:H{linha}"
    ws.page_margins.left = ws.page_margins.right = 0.5

    wb.save(caminho)