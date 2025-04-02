from django.contrib import admin
from .models import FamilyMember, Tag, Transaction, Expense, Income

admin.site.register(FamilyMember)
admin.site.register(Tag)
admin.site.register(Transaction)
admin.site.register(Expense)
admin.site.register(Income)
