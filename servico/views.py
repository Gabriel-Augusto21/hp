from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Servico
from dentista.models import Dentista
from django.core.paginator import Paginator

def servico(request):
    servicos = Servico.objects.all()
    status = request.GET.get('status')
    dentista = request.GET.get('dentista')

    if status:
        servicos = servicos.filter(status=status)

    if dentista:
        servicos = servicos.filter(dentista_id=dentista)

    paginator = Paginator(servicos, 8)
    page = request.GET.get('page')

    servicos_paginados = paginator.get_page(page)

    page_range = list(paginator.get_elided_page_range(
        servicos_paginados.number,
        on_each_side=2,
        on_ends=1
    ))

    return render(request, 'servico.html', {
        'servicos': servicos_paginados,
        'page_range': page_range,
        'dentistas': Dentista.objects.all(),
        'statuses': Servico.STATUS_CHOICES
    })

def parse_decimal(value):
    if not value:
        return 0
    value = value.replace('.', '').replace(',', '.')
    try:
        from decimal import Decimal
        return Decimal(value)
    except:
        return 0

def detalhe_servico(request, pk):
    servico = get_object_or_404(Servico, pk=pk)
    return render(request, 'detalhe_servico.html', {'servico': servico})


def criar_servico(request):
    if request.method == 'POST':
        try:
            Servico.objects.create(
                dentista_id=request.POST.get('dentista') or None,
                paciente=request.POST.get('paciente', ''),
                tipo_protese=request.POST.get('tipo_protese'),
                material=request.POST.get('material'),
                descricao=request.POST.get('descricao'),
                data_entrada=request.POST.get('data_entrada'),
                data_prevista_saida=request.POST.get('data_prevista_saida') or None,
                valor_servico=parse_decimal(request.POST.get('valor_servico')),
                status=request.POST.get('status', 'REC')
            )
            messages.success(request, 'Serviço criado com sucesso!')
            return redirect('servico:servico')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    
    return render(request, 'form_servico.html', {
        'dentistas': Dentista.objects.all(),
        'statuses': Servico.STATUS_CHOICES
    })


def editar_servico(request, pk):
    servico = get_object_or_404(Servico, pk=pk)
    if request.method == 'POST':
        servico.dentista_id = request.POST.get('dentista') or None
        servico.paciente = request.POST.get('paciente', '')
        servico.tipo_protese = request.POST.get('tipo_protese')
        servico.material = request.POST.get('material')
        servico.descricao = request.POST.get('descricao')
        servico.data_entrada = request.POST.get('data_entrada')
        servico.data_prevista_saida = request.POST.get('data_prevista_saida') or None
        servico.valor_servico = parse_decimal(request.POST.get('valor_servico'))
        servico.valor_pago = request.POST.get('valor_pago') or 0
        servico.status = request.POST.get('status')
        servico.save()
        messages.success(request, 'Serviço atualizado!')
        return redirect('servico:detalhe_servico', pk=servico.pk)
    
    return render(request, 'form_servico.html', {
        'servico': servico,
        'edit': True,
        'dentistas': Dentista.objects.all(),
        'statuses': Servico.STATUS_CHOICES
    })


def deletar_servico(request, pk):
    servico = get_object_or_404(Servico, pk=pk)
    if request.method == 'POST':
        servico.delete()
        messages.success(request, 'Serviço deletado!')
        return redirect('servico:servico')
    return render(request, 'deletar_servico.html', {'servico': servico})