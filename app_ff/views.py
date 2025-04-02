from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Transaction, Expense, Income, Tag, FamilyMember

# Serializers
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

    def validate(self, data):
        """Valida os campos de recorrência e parcelas"""
        recurrence = data.get('recurrence', 'one_time')
        total_installments = data.get('total_installments')

        if recurrence == 'one_time' and total_installments:
            raise serializers.ValidationError({'total_installments': 'Cannot set installments for one-time transactions.'})

        if recurrence == 'installment' and not total_installments:
            raise serializers.ValidationError({'total_installments': 'This field is required for installment transactions.'})

        if recurrence == 'recurring' and total_installments:
            raise serializers.ValidationError({'total_installments': 'Recurring transactions cannot have installments.'})

        if 'member' not in data:
            raise serializers.ValidationError({'member': 'This field is required.'})

        if 'tag' not in data:
            data['tag'] = Tag.objects.get_or_create(name="Other", type="expense")[0]

        return data


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['status']

class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = '__all__'
        read_only_fields = ['status']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = '__all__'

# ViewSets
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def destroy(self, request, *args, **kwargs):
        transaction = self.get_object()
        if transaction.status != 'pending':
            return Response({'error': 'Only pending transactions can be deleted'}, status=status.HTTP_400_BAD_REQUEST)
        transaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def post_transaction(self, request, pk=None):
        transaction = get_object_or_404(Transaction, pk=pk)
        if transaction.status != 'pending':
            return Response({'error': 'Transaction already posted'}, status=status.HTTP_400_BAD_REQUEST)
        transaction.post()
        return Response({'message': 'Transaction posted successfully'})

class ExpenseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        expense = get_object_or_404(Expense, pk=pk)
        expense.clear()
        return Response({'message': 'Expense cleared successfully'})

class IncomeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        income = get_object_or_404(Income, pk=pk)
        income.clear()
        return Response({'message': 'Income cleared successfully'})

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class FamilyMemberViewSet(viewsets.ModelViewSet):
    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer
