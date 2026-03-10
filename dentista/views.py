from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Dentista
from django.core.paginator import Paginator

def dentista(request):
    dentistas = Dentista.objects.all()
    paginator = Paginator(dentistas, 7)
    page = request.GET.get('page')
    dentistas_paginados = paginator.get_page(page)
    page_range = list(paginator.get_elided_page_range(
        dentistas_paginados.number,
        on_each_side=2,
        on_ends=1
    ))
    return render(request, 'dentista.html', {'dentistas': dentistas_paginados, 'page_range': page_range})

def detalhe_dentista(request, pk):
    dentista = get_object_or_404(Dentista, pk=pk)
    servicos = dentista.servicos.all()
    return render(request, 'detalhe_dentista.html', {'dentista': dentista, 'servicos': servicos})

def criar_dentista(request):
    if request.method == 'POST':
        try:
            Dentista.objects.create(
                nome=request.POST.get('nome'),
                email=request.POST.get('email'),
                telefone=request.POST.get('telefone'),
                especialidade=request.POST.get('especialidade'),
                cro=request.POST.get('cro')
            )
            messages.success(request, 'Dentista criado com sucesso!')
            return redirect('dentista:dentista')
        except Exception as e:
            messages.error(request, f'Erro: {str(e)}')
    return render(request, 'form_dentista.html')

def editar_dentista(request, pk):
    dentista = get_object_or_404(Dentista, pk=pk)
    if request.method == 'POST':
        dentista.nome = request.POST.get('nome')
        dentista.email = request.POST.get('email')
        dentista.telefone = request.POST.get('telefone')
        dentista.especialidade = request.POST.get('especialidade')
        dentista.cro = request.POST.get('cro')
        dentista.save()
        messages.success(request, 'Dentista atualizado!')
        return redirect('dentista:detalhe_dentista', pk=dentista.pk)
    return render(request, 'form_dentista.html', {'dentista': dentista, 'edit': True})

def deletar_dentista(request, pk):
    dentista = get_object_or_404(Dentista, pk=pk)
    if request.method == 'POST':
        dentista.delete()
        messages.success(request, 'Dentista deletado!')
        return redirect('dentista:dentista')
    return render(request, 'deletar_dentista.html', {'dentista': dentista})
