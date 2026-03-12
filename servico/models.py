from django.db import models
from dentista.models import Dentista


class Servico(models.Model):
    STATUS_CHOICES = [
        ('REC', 'Recebido'),
        ('PROD', 'Em Produção'),
        ('FIN', 'Finalizado'),
        ('ENT', 'Entregue'),
        ('CAN', 'Cancelado'),
        ('PRO', 'Provando'),
    ]
    
    dentista = models.ForeignKey(Dentista, on_delete=models.CASCADE, null=True, blank=True, related_name='servicos')
    paciente = models.CharField(max_length=200, blank=True)
    
    tipo_protese = models.CharField(max_length=100)
    material = models.CharField(max_length=100, blank=True)
    descricao = models.TextField(blank=True)
    
    data_entrada = models.DateField()
    data_prevista_saida = models.DateField(blank=True, null=True)
    data_saida = models.DateField(blank=True, null=True)
    
    valor_servico = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_length=4, choices=STATUS_CHOICES, default='REC')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-data_entrada']
    
    def __str__(self):
        return f"{self.tipo_protese} - {self.dentista.nome}"
    
    @property
    def saldo(self):
        return self.valor_servico - self.valor_pago
    
    @property
    def atrasado(self):
        from django.utils import timezone
        if self.status != 'ENT' and self.status != 'FIN' and self.status != 'CAN' and self.status != 'PRO' and self.data_prevista_saida:
            return self.data_prevista_saida < timezone.now().date()
        return False