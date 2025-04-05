import uuid
from datetime import timedelta, date
from django.db import models

# Lista de opções para o campo "status" das transações, despesas e receitas
STATUS_CHOICES = [
    ('pending', 'Pending'),   # Pendente
    ('posted', 'Posted'),     # Registrado
    ('cleared', 'Cleared')    # Concluído
]

# Lista de opções para o campo "type" (tipo de transação)
TYPE_CHOICES = [
    ('income', 'Income'),     # Receita
    ('expense', 'Expense')    # Despesa
]

# Lista de opções para o campo "recurrence" (recorrência)
RECURRENCE_CHOICES = [
    ('one_time', 'One-Time'),         # Pagamento único
    ('recurring', 'Recurring'),       # Pagamento recorrente (mensal, por exemplo)
    ('installment', 'Installment')    # Parcelado
]

# Modelo que representa um membro da família
class FamilyMember(models.Model):
    # Tipos de relacionamento com o membro da família
    RELATIONSHIP_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('other', 'Other')
    ]

    # ID único gerado automaticamente (UUID)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)  # Nome do membro
    relationship = models.CharField(max_length=10, choices=RELATIONSHIP_CHOICES)  # Tipo de relação

    # Representação textual do objeto
    def __str__(self):
        return self.name

# Modelo que representa uma tag/categoria da transação
class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, default="Other")  # Nome da tag
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)  # Tipo: receita ou despesa

    def __str__(self):
        return self.name

# Função auxiliar para retornar a tag padrão (caso nenhuma seja fornecida)
def get_default_tag():
    # Busca ou cria a tag chamada "Other" do tipo "expense" e retorna seu ID
    return Tag.objects.get_or_create(name="Other", type="expense")[0].id

# Modelo que representa uma transação financeira
class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)  # Data/hora de criação
    due_date = models.DateField()  # Data de vencimento
    description = models.TextField()  # Descrição da transação
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)  # Valor total
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)  # Tipo: receita ou despesa
    recurrence = models.CharField(max_length=11, choices=RECURRENCE_CHOICES, default='one_time')  # Recorrência
    total_installments = models.IntegerField(null=True, blank=True)  # Total de parcelas (se houver)
    member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE)  # Membro associado
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, default=get_default_tag)  # Categoria/tag da transação
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Status da transação

    def __str__(self):
        return f"{self.description} - {self.status}"

    def post(self):
        """
        Método para "postar" a transação.
        Dependendo do tipo e da recorrência, cria objetos de Expense ou Income.
        """

        # Verifica se a transação ainda está pendente
        if self.status != 'pending':
            raise ValueError("Only pending transactions can be posted.")

        # Se for uma despesa
        if self.type == 'expense':
            # Se for parcelada e tiver número de parcelas
            if self.recurrence == 'installment' and self.total_installments:
                for i in range(self.total_installments):
                    # Define a data da parcela (incrementa o mês)
                    installment_due_date = self.due_date.replace(month=self.due_date.month + i)
                    # Cria uma despesa para cada parcela
                    Expense.objects.create(
                        transaction=self,
                        amount=self.total_amount / self.total_installments,
                        date=installment_due_date,
                        current_installment=i + 1,
                        total_installments=self.total_installments,
                    )
            # Se for uma despesa recorrente (ex: mensal)
            elif self.recurrence == 'recurring':
                for i in range(12):  # Cria para os próximos 12 meses
                    recurring_due_date = self.due_date.replace(month=self.due_date.month + i) - timedelta(days=10)
                    Expense.objects.create(
                        transaction=self,
                        amount=self.total_amount,
                        date=recurring_due_date,
                        current_installment=None,
                        total_installments=None
                    )
            # Se for uma despesa única
            else:
                Expense.objects.create(
                    transaction=self,
                    amount=self.total_amount,
                    date=self.due_date,
                    current_installment=1,
                    total_installments=1
                )
        else:
            # Se for receita, cria um único Income
            Income.objects.create(transaction=self, amount=self.total_amount, date=self.due_date)

        # Atualiza o status da transação para "posted"
        self.status = 'posted'
        self.save()

# Modelo que representa uma despesa (gerada a partir de uma transação de despesa)
class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="expenses")  # Transação associada
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Valor da despesa
    date = models.DateField()  # Data da despesa
    current_installment = models.IntegerField(null=True, blank=True)  # Número da parcela (se aplicável)
    total_installments = models.IntegerField(null=True, blank=True)  # Total de parcelas (se aplicável)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Status da despesa

    def __str__(self):
        return f"Expense of $ {self.amount} - {self.status}"

    def clear(self):
        """
        Marca a despesa como concluída.
        """
        self.status = 'cleared'
        self.save()

# Modelo que representa uma receita (gerada a partir de uma transação de receita)
class Income(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)  # Transação associada
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Valor da receita
    date = models.DateField()  # Data da receita
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Status da receita

    def __str__(self):
        return f"Income of $ {self.amount} - {self.status}"

    def clear(self):
        """
        Marca a receita como concluída.
        """
        self.status = 'cleared'
        self.save()
