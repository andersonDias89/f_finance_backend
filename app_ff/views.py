# Importações da biblioteca do Django REST Framework
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

# Função utilitária do Django para buscar um objeto ou retornar erro 404
from django.shortcuts import get_object_or_404

# Importação dos modelos usados nesta API
from .models import Transaction, Expense, Income, Tag, FamilyMember

# -------------------- SERIALIZERS --------------------

class TransactionSerializer(serializers.ModelSerializer):
    tag_detail = serializers.SerializerMethodField()
    member_detail = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = '__all__'  # Inclui os campos normais
        extra_fields = ['tag_detail', 'member_detail']
        read_only_fields = ['tag_detail', 'member_detail']

    def get_tag_detail(self, obj):
        if obj.tag:
            return {
                "id": obj.tag.id,
                "name": obj.tag.name,
                "type": obj.tag.type
            }
        return None

    def get_member_detail(self, obj):
        if obj.member:
            return {
                "id": obj.member.id,
                "name": obj.member.name
            }
        return None

    def validate(self, data):
        """
        Método de validação customizado para verificar se os dados de recorrência e parcelas
        estão corretos de acordo com a lógica de negócio.
        """
        recurrence = data.get('recurrence', 'one_time')
        total_installments = data.get('total_installments')

        if recurrence == 'one_time' and total_installments:
            raise serializers.ValidationError({
                'total_installments': 'Cannot set installments for one-time transactions.'
            })

        if recurrence == 'installment' and not total_installments:
            raise serializers.ValidationError({
                'total_installments': 'This field is required for installment transactions.'
            })

        if recurrence == 'recurring' and total_installments:
            raise serializers.ValidationError({
                'total_installments': 'Recurring transactions cannot have installments.'
            })

        if 'member' not in data:
            raise serializers.ValidationError({
                'member': 'This field is required.'
            })

        if 'tag' not in data:
            data['tag'] = Tag.objects.get_or_create(name="Other", type="expense")[0]

        return data



# Serializer para o modelo Expense
class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['status']  # Campo status só pode ser lido, não escrito

# Serializer para o modelo Income
class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = '__all__'
        read_only_fields = ['status']  # Campo status só pode ser lido, não escrito

# Serializer para o modelo Tag
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

# Serializer para o modelo FamilyMember
class FamilyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyMember
        fields = '__all__'

# -------------------- VIEWSETS --------------------

# ViewSet para operações com transações (CRUD completo)
class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()  # Consulta todas as transações
    serializer_class = TransactionSerializer  # Usa o serializer correspondente

    def destroy(self, request, *args, **kwargs):
        """
        Sobrescreve o método DELETE para impedir exclusão de transações já postadas.
        Apenas transações pendentes podem ser deletadas.
        """
        transaction = self.get_object()
        if transaction.status != 'pending':
            return Response({'error': 'Only pending transactions can be deleted'}, status=status.HTTP_400_BAD_REQUEST)
        transaction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def post_transaction(self, request, pk=None):
        """
        Ação personalizada que permite "postar" uma transação manualmente.
        Isso cria os objetos de despesa ou receita correspondentes.
        """
        transaction = get_object_or_404(Transaction, pk=pk)
        if transaction.status != 'pending':
            return Response({'error': 'Transaction already posted'}, status=status.HTTP_400_BAD_REQUEST)
        transaction.post()
        return Response({'message': 'Transaction posted successfully'})

# ViewSet somente leitura para visualizar despesas
class ExpenseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Expense.objects.all()  # Consulta todas as despesas
    serializer_class = ExpenseSerializer

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """
        Ação personalizada para marcar uma despesa como "cleared" (concluída).
        """
        expense = get_object_or_404(Expense, pk=pk)
        expense.clear()
        return Response({'message': 'Expense cleared successfully'})

# ViewSet somente leitura para visualizar receitas
class IncomeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Income.objects.all()  # Consulta todas as receitas
    serializer_class = IncomeSerializer

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """
        Ação personalizada para marcar uma receita como "cleared" (concluída).
        """
        income = get_object_or_404(Income, pk=pk)
        income.clear()
        return Response({'message': 'Income cleared successfully'})

# ViewSet completo (CRUD) para as tags
class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

# ViewSet completo (CRUD) para os membros da família
class FamilyMemberViewSet(viewsets.ModelViewSet):
    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer
