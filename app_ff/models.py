from django.db import models

from django.db import models

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('income', 'Income'),   # Entrada
        ('expense', 'Expense'), # Saída
    ]

    type = models.CharField(max_length=7, choices=TRANSACTION_TYPES)  # Income ou Expense
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Valor com até 10 dígitos e 2 casas decimais
    description = models.CharField(max_length=50)  # Descrição curta
    created_at = models.DateTimeField(auto_now_add=True)  # Criado automaticamente
    updated_at = models.DateTimeField(auto_now=True)  # Atualizado automaticamente

    def __str__(self):
        return f"{self.type} - ${self.amount:.2f}"

