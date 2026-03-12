from datetime import date, timedelta
from io import BytesIO
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from dentista.models import Dentista
from servico.models import Servico
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

_AZUL_ESC  = colors.HexColor("#1a3c5e")
_AZUL_MED  = colors.HexColor("#2980b9")
_AZUL_CLA  = colors.HexColor("#d6eaf8")
_VERMELHO  = colors.HexColor("#c0392b")
_CINZA_CLA = colors.HexColor("#f2f3f4")
_CINZA_MED = colors.HexColor("#bdc3c7")
_MARROM    = colors.HexColor("#a0522d")

def _estilos():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "titulo", parent=base["Title"],
            fontSize=18, textColor=_AZUL_ESC, spaceAfter=2,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
        ),
        "sub": ParagraphStyle(
            "sub", parent=base["Normal"],
            fontSize=10, textColor=_AZUL_MED, spaceAfter=1,
            fontName="Helvetica", alignment=TA_CENTER,
        ),
        "rodape": ParagraphStyle(
            "rodape", parent=base["Normal"],
            fontSize=8, textColor=_CINZA_MED, alignment=TA_CENTER,
        ),
    }


def _cabecalho(story, titulo, subtitulo=None, periodo=None):
    e = _estilos()
    story.append(Paragraph("Laboratório HP2", e["sub"]))
    story.append(Paragraph(titulo, e["titulo"]))
    if subtitulo:
        story.append(Paragraph(subtitulo, e["sub"]))
    if periodo:
        story.append(Paragraph(f"Período: {periodo}", e["sub"]))
    story.append(Paragraph(
        f"Gerado em: {date.today().strftime('%d/%m/%Y')}", e["rodape"]
    ))
    story.append(HRFlowable(
        width="100%", thickness=1.5, color=_AZUL_ESC, spaceAfter=10
    ))


def _ts(header_color=None):
    hc = header_color or _AZUL_ESC
    return TableStyle([
        ("BACKGROUND",     (0,  0), (-1,  0), hc),
        ("TEXTCOLOR",      (0,  0), (-1,  0), colors.white),
        ("FONTNAME",       (0,  0), (-1,  0), "Helvetica-Bold"),
        ("FONTSIZE",       (0,  0), (-1,  0), 9),
        ("ALIGN",          (0,  0), (-1,  0), "CENTER"),
        ("TOPPADDING",     (0,  0), (-1,  0), 6),
        ("BOTTOMPADDING",  (0,  0), (-1,  0), 6),
        ("FONTNAME",       (0,  1), (-1, -1), "Helvetica"),
        ("FONTSIZE",       (0,  1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0,  1), (-1, -1), [colors.white, _CINZA_CLA]),
        ("VALIGN",         (0,  0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",     (0,  1), (-1, -1), 4),
        ("BOTTOMPADDING",  (0,  1), (-1, -1), 4),
        ("GRID",           (0,  0), (-1, -1), 0.4, _CINZA_MED),
        ("LINEBELOW",      (0,  0), (-1,  0), 1.5, _AZUL_MED),
    ])


def _bloco_totais(story, dados: dict):
    linhas = [["Resumo", "Valor"]] + [[k, v] for k, v in dados.items()]
    t = Table(linhas, colWidths=[10*cm, 5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0, 0), (-1,  0), _AZUL_MED),
        ("TEXTCOLOR",      (0, 0), (-1,  0), colors.white),
        ("FONTNAME",       (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("GRID",           (0, 0), (-1, -1), 0.4, _CINZA_MED),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_AZUL_CLA, colors.white]),
        ("ALIGN",          (1, 0), (1,  -1), "RIGHT"),
    ]))
    story.append(Spacer(1, 0.4*cm))
    story.append(t)


def _r(v) -> str:
    return f"R$ {float(v or 0):.2f}"


def _fmt_data(d) -> str:
    return d.strftime("%d/%m/%Y") if d else "-"


def _doc_retrato(buf):
    return SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm,  bottomMargin=2*cm)


def _doc_paisagem(buf):
    return SimpleDocTemplate(buf, pagesize=landscape(A4),
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=2*cm,   bottomMargin=2*cm)


def _pdf_response(conteudo: bytes, nome: str) -> HttpResponse:
    resp = HttpResponse(conteudo, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{nome}"'
    return resp

def _pdf_dashboard(ctx) -> bytes:
    buf = BytesIO()
    doc = _doc_retrato(buf)
    story = []
    _cabecalho(story, "Dashboard Geral")
    dados = [
        ["Indicador",         "Valor"],
        ["Total de Serviços", str(ctx["total_servicos"])],
        ["Recebidos",         str(ctx["por_status"].get("REC",  0))],
        ["Em Produção",       str(ctx["por_status"].get("PROD", 0))],
        ["Finalizados",       str(ctx["por_status"].get("FIN",  0))],
        ["Entregues",         str(ctx["por_status"].get("ENT",  0))],
        ["Cancelados",        str(ctx["por_status"].get("CAN",  0))],
        ["Provando",         str(ctx["por_status"].get("PRO",  0))],
        ["Atrasados",         str(ctx["servicos_atrasados"])],
        ["Faturamento Total", _r(ctx["valor_total"])],
    ]
    t = Table(dados, colWidths=[9*cm, 6*cm])
    t.setStyle(_ts())
    story.append(t)
    doc.build(story)
    return buf.getvalue()


def _pdf_financeiro(servicos, vt, periodo=None) -> bytes:
    buf = BytesIO()
    doc = _doc_paisagem(buf)
    story = []
    _cabecalho(story, "Relatório Financeiro", periodo=periodo)
    linhas = [["Prótese", "Dentista", "Paciente", "Entrada", "Vl. Serviço", "Status"]]
    for s in servicos:
        linhas.append([
            s.tipo_protese,
            s.dentista.nome if s.dentista else "-",
            s.paciente or "-",
            _fmt_data(s.data_entrada),
            _r(s.valor_servico),
            s.get_status_display(),
        ])
    cw = [4*cm, 3.5*cm, 3.5*cm, 3*cm, 3.5*cm, 3.5*cm]
    t = Table(linhas, colWidths=cw, repeatRows=1)
    t.setStyle(_ts())
    story.append(t)
    _bloco_totais(story, {"Faturamento Total": _r(vt)})
    doc.build(story)
    return buf.getvalue()


def _pdf_dentistas(dentistas, periodo=None) -> bytes:
    buf = BytesIO()
    doc = _doc_retrato(buf)
    story = []
    _cabecalho(story, "Receita por Dentista", periodo=periodo)
    linhas = [["Dentista", "Qtd.", "Faturamento"]]
    fat_total = 0
    for d in dentistas:
        fat = float(d.valor_total or 0)
        fat_total += fat
        linhas.append([d.nome, str(d.total_servicos), _r(fat)])
    cw = [9*cm, 3*cm, 5*cm]
    t = Table(linhas, colWidths=cw, repeatRows=1)
    t.setStyle(_ts())
    story.append(t)
    _bloco_totais(story, {"Faturamento Total": _r(fat_total)})
    doc.build(story)
    return buf.getvalue()


def _pdf_atrasados(servicos) -> bytes:
    buf = BytesIO()
    doc = _doc_paisagem(buf)
    story = []
    _cabecalho(story, "Serviços Atrasados",
               subtitulo=f"{len(servicos)} serviço(s) em atraso")
    linhas = [["Prótese", "Dentista", "Paciente", "Saída Prevista", "Dias Atraso", "Status", "Valor"]]
    for s in servicos:
        linhas.append([
            s.tipo_protese,
            s.dentista.nome if s.dentista else "-",
            s.paciente or "-",
            _fmt_data(s.data_prevista_saida),
            f"{s.dias_atraso} dia(s)",
            s.get_status_display(),
            _r(s.valor_servico),
        ])
    cw = [3.5*cm, 3.5*cm, 3*cm, 3*cm, 2.5*cm, 3*cm, 3*cm]
    t = Table(linhas, colWidths=cw, repeatRows=1)
    style = _ts(header_color=_VERMELHO)
    for i in range(1, len(linhas)):
        style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fde8e8"))
    t.setStyle(style)
    story.append(t)
    doc.build(story)
    return buf.getvalue()


def _pdf_status(dados_status, periodo=None) -> bytes:
    buf = BytesIO()
    doc = _doc_retrato(buf)
    story = []
    _cabecalho(story, "Serviços por Status", periodo=periodo)
    total_qtd = sum(d["quantidade"] for d in dados_status)
    total_fat = sum(d["valor_total"] for d in dados_status)
    linhas = [["Status", "Quantidade", "Faturamento", "% do Total"]]
    for d in dados_status:
        pct = (d["quantidade"] / total_qtd * 100) if total_qtd else 0
        linhas.append([d["status_display"], str(d["quantidade"]),
                       _r(d["valor_total"]), f"{pct:.1f}%"])
    linhas.append(["TOTAL", str(total_qtd), _r(total_fat), "100%"])
    cw = [6*cm, 3*cm, 4*cm, 3*cm]
    t = Table(linhas, colWidths=cw)
    style = _ts()
    style.add("BACKGROUND", (0, -1), (-1, -1), _AZUL_ESC)
    style.add("TEXTCOLOR",  (0, -1), (-1, -1), colors.white)
    style.add("FONTNAME",   (0, -1), (-1, -1), "Helvetica-Bold")
    t.setStyle(style)
    story.append(t)
    doc.build(story)
    return buf.getvalue()


def _pdf_periodo(servicos, di, df) -> bytes:
    buf = BytesIO()
    doc = _doc_paisagem(buf)
    story = []
    periodo = f"{di.strftime('%d/%m/%Y')} a {df.strftime('%d/%m/%Y')}"
    _cabecalho(story, "Relatório por Período", periodo=periodo)
    linhas = [["Prótese", "Dentista", "Paciente", "Entrada", "Saída Prev.", "Status", "Vl. Serviço"]]
    fat_total = 0
    for s in servicos:
        fat_total += float(s.valor_servico or 0)
        linhas.append([
            s.tipo_protese,
            s.dentista.nome if s.dentista else "-",
            s.paciente or "-",
            _fmt_data(s.data_entrada),
            _fmt_data(s.data_prevista_saida),
            s.get_status_display(),
            _r(s.valor_servico),
        ])
    cw = [4*cm, 3.5*cm, 3.5*cm, 2.8*cm, 2.8*cm, 3*cm, 3.4*cm]
    t = Table(linhas, colWidths=cw, repeatRows=1)
    t.setStyle(_ts())
    story.append(t)
    _bloco_totais(story, {"Faturamento no Período": _r(fat_total)})
    doc.build(story)
    return buf.getvalue()


def _pdf_detalhe_dentista(dentista, servicos, vt, periodo=None) -> bytes:
    buf = BytesIO()
    doc = _doc_paisagem(buf)
    story = []
    _cabecalho(story, f"Serviços — {dentista.nome}", periodo=periodo)
    linhas = [["Prótese", "Paciente", "Entrada", "Saída Prev.", "Status", "Valor"]]
    for s in servicos:
        linhas.append([
            s.tipo_protese,
            s.paciente or "-",
            _fmt_data(s.data_entrada),
            _fmt_data(s.data_prevista_saida),
            s.get_status_display(),
            _r(s.valor_servico),
        ])
    cw = [5*cm, 5*cm, 3*cm, 3*cm, 3.5*cm, 3.5*cm]
    t = Table(linhas, colWidths=cw, repeatRows=1)
    t.setStyle(_ts())
    story.append(t)
    _bloco_totais(story, {"Faturamento Total": _r(vt)})
    doc.build(story)
    return buf.getvalue()

def _filtros_periodo(request):
    hoje = date.today()
    try:
        di = date.fromisoformat(request.GET.get("data_inicio", ""))
    except ValueError:
        di = hoje - timedelta(days=30)
    try:
        df = date.fromisoformat(request.GET.get("data_fim", ""))
    except ValueError:
        df = hoje
    return di, df


def _agg_fat(qs):
    return qs.aggregate(total=Sum("valor_servico"))["total"] or 0


def _periodo_str(di, df) -> str:
    return f"{di.strftime('%d/%m/%Y')} a {df.strftime('%d/%m/%Y')}"


def dashboard(request):
    hoje = timezone.now().date()
    qs = Servico.objects.all()

    por_status_qs = qs.values("status").annotate(qtd=Count("id"))
    por_status = {item["status"]: item["qtd"] for item in por_status_qs}

    atrasados = qs.filter(
        ~Q(status__in=["ENT", "CAN", "PRO", "FIN"]),
        data_prevista_saida__lt=hoje,
    ).count()

    valor_total = _agg_fat(qs)

    ctx = {
        "total_servicos":     qs.count(),
        "por_status":         por_status,
        "servicos_atrasados": atrasados,
        "valor_total":        valor_total,
        "qtd_recebido":       por_status.get("REC",  0),
        "qtd_producao":       por_status.get("PROD", 0),
        "qtd_finalizado":     por_status.get("FIN",  0),
        "qtd_entregue":       por_status.get("ENT",  0),
        "qtd_cancelado":      por_status.get("CAN",  0),
        "qtd_provando":       por_status.get("PRO",  0),
    }
    if request.GET.get("pdf"):
        return _pdf_response(_pdf_dashboard(ctx), "dashboard.pdf")
    return render(request, "dashboard.html", ctx)


def financeiro(request):
    di, df = _filtros_periodo(request)
    qs = (Servico.objects
          .filter(data_entrada__gte=di, data_entrada__lte=df)
          .select_related("dentista")
          .order_by("data_entrada"))
    vt = _agg_fat(qs)

    ctx = {"servicos": qs, "valor_total": vt, "data_inicio": di, "data_fim": df}
    if request.GET.get("pdf"):
        return _pdf_response(
            _pdf_financeiro(qs, vt, _periodo_str(di, df)), "financeiro.pdf"
        )
    return render(request, "financeiro.html", ctx)


def servicos_por_dentista(request):
    di, df = _filtros_periodo(request)
    dentistas = (Dentista.objects
                 .filter(servicos__data_entrada__gte=di,
                         servicos__data_entrada__lte=df)
                 .annotate(
                     total_servicos=Count("servicos"),
                     valor_total=Sum("servicos__valor_servico"),
                 )
                 .distinct()
                 .order_by("nome"))

    ctx = {"dentistas": dentistas, "data_inicio": di, "data_fim": df}
    if request.GET.get("pdf"):
        return _pdf_response(
            _pdf_dentistas(dentistas, _periodo_str(di, df)), "dentistas.pdf"
        )
    return render(request, "servicos_dentista.html", ctx)


def detalhe_dentista(request, pk):
    dentista = Dentista.objects.get(pk=pk)
    di, df = _filtros_periodo(request)

    qs = (Servico.objects
          .filter(dentista=dentista,
                  data_entrada__gte=di,
                  data_entrada__lte=df)
          .order_by("-data_entrada"))

    status_filtro = request.GET.get("status", "")
    if status_filtro:
        qs = qs.filter(status=status_filtro)

    vt = _agg_fat(qs)

    ctx = {
        "dentista":     dentista,
        "servicos":     qs,
        "valor_total":  vt,
        "data_inicio":  di,
        "data_fim":     df,
        "status_filtro": status_filtro,
        "statuses":     Servico.STATUS_CHOICES,
    }
    if request.GET.get("pdf"):
        return _pdf_response(
            _pdf_detalhe_dentista(dentista, qs, vt, _periodo_str(di, df)),
            f"dentista_{dentista.pk}.pdf"
        )
    return render(request, "detalhe_dentista.html", ctx)


def servicos_atrasados(request):
    hoje = timezone.now().date()
    qs = (Servico.objects
          .filter(~Q(status__in=["ENT", "CAN", "PRO", "FIN"]),
                  data_prevista_saida__lt=hoje)
          .select_related("dentista")
          .order_by("data_prevista_saida"))

    servicos = []
    for s in qs:
        s.dias_atraso = (hoje - s.data_prevista_saida).days if s.data_prevista_saida else 0
        servicos.append(s)

    ctx = {"servicos": servicos, "hoje": hoje}
    if request.GET.get("pdf"):
        return _pdf_response(_pdf_atrasados(servicos), "atrasados.pdf")
    return render(request, "atrasados.html", ctx)


def servicos_por_status(request):
    di, df = _filtros_periodo(request)
    qs = Servico.objects.filter(data_entrada__gte=di, data_entrada__lte=df)

    status_map = dict(Servico.STATUS_CHOICES)
    grupos = (qs.values("status")
                .annotate(quantidade=Count("id"),
                          valor_total=Sum("valor_servico"))
                .order_by("status"))

    dados_status = [
        {
            "status":         g["status"],
            "status_display": status_map.get(g["status"], g["status"]),
            "quantidade":     g["quantidade"],
            "valor_total":    float(g["valor_total"] or 0),
        }
        for g in grupos
    ]

    ctx = {"dados_status": dados_status, "data_inicio": di, "data_fim": df}
    if request.GET.get("pdf"):
        return _pdf_response(
            _pdf_status(dados_status, _periodo_str(di, df)), "status.pdf"
        )
    return render(request, "por_status.html", ctx)


def relatorio_periodo(request):
    di, df = _filtros_periodo(request)
    qs = (Servico.objects
          .filter(data_entrada__gte=di, data_entrada__lte=df)
          .select_related("dentista")
          .order_by("data_entrada"))
    vt = _agg_fat(qs)

    ctx = {"servicos": qs, "valor_total": vt, "data_inicio": di, "data_fim": df}
    if request.GET.get("pdf"):
        return _pdf_response(_pdf_periodo(qs, di, df), "periodo.pdf")
    return render(request, "periodo.html", ctx)