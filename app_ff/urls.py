from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransactionViewSet, ExpenseViewSet, IncomeViewSet, TagViewSet, FamilyMemberViewSet

router = DefaultRouter()
router.register(r'transactions', TransactionViewSet)
router.register(r'expenses', ExpenseViewSet)
router.register(r'incomes', IncomeViewSet)
router.register(r'tags', TagViewSet)
router.register(r'family-members', FamilyMemberViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
