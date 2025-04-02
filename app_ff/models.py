import uuid
from datetime import timedelta, date
from django.db import models

# Status choices
STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('posted', 'Posted'),
    ('cleared', 'Cleared')
]

# Type choices
TYPE_CHOICES = [
    ('income', 'Income'),
    ('expense', 'Expense')
]

# Recurrence choices
RECURRENCE_CHOICES = [
    ('one_time', 'One-Time'),
    ('recurring', 'Recurring'),
    ('installment', 'Installment')
]

# Model for Family Member
class FamilyMember(models.Model):
    RELATIONSHIP_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('son', 'Son'),
        ('daughter', 'Daughter'),
        ('other', 'Other')
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    relationship = models.CharField(max_length=10, choices=RELATIONSHIP_CHOICES)

    def __str__(self):
        return self.name

# Model for Tag
class Tag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, default="Other")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    def __str__(self):
        return self.name

# Default function for Tag
def get_default_tag():
    return Tag.objects.get_or_create(name="Other", type="expense")[0].id

# Model for Transaction
class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    description = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    recurrence = models.CharField(max_length=11, choices=RECURRENCE_CHOICES, default='one_time')
    total_installments = models.IntegerField(null=True, blank=True)
    member = models.ForeignKey(FamilyMember, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, default=get_default_tag)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.description} - {self.status}"

    def post(self):
        """Posts the transaction and generates corresponding expenses or incomes"""
        if self.status != 'pending':
            raise ValueError("Only pending transactions can be posted.")

        if self.type == 'expense':
            if self.recurrence == 'installment' and self.total_installments:
                for i in range(self.total_installments):
                    installment_due_date = self.due_date.replace(month=self.due_date.month + i)
                    Expense.objects.create(
                        transaction=self,
                        amount=self.total_amount / self.total_installments,
                        date=installment_due_date,
                        current_installment=i + 1,
                        total_installments=self.total_installments,
                    )
            elif self.recurrence == 'recurring':
                for i in range(12):  # Criar para 12 meses automaticamente
                    recurring_due_date = self.due_date.replace(month=self.due_date.month + i) - timedelta(days=10)
                    Expense.objects.create(
                        transaction=self,
                        amount=self.total_amount,
                        date=recurring_due_date,
                        current_installment=None,
                        total_installments=None
                    )
            else:
                Expense.objects.create(
                    transaction=self,
                    amount=self.total_amount,
                    date=self.due_date,
                    current_installment=1,
                    total_installments=1
                )
        else:
            Income.objects.create(transaction=self, amount=self.total_amount, date=self.due_date)

        self.status = 'posted'
        self.save()

# Model for Expense (created when an expense transaction is posted)
class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="expenses")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    current_installment = models.IntegerField(null=True, blank=True)
    total_installments = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Expense of $ {self.amount} - {self.status}"

    def clear(self):
        """Clears the expense and finalizes its lifecycle"""
        self.status = 'cleared'
        self.save()

# Model for Income (created when an income transaction is posted)
class Income(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Income of $ {self.amount} - {self.status}"

    def clear(self):
        """Clears the income and finalizes its lifecycle"""
        self.status = 'cleared'
        self.save()
