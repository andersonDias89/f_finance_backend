from django.http import JsonResponse

def hello_world(request):
    """
    A simple view that returns a JSON response with a greeting message.
    """
    return JsonResponse({'message': 'Hello, world!'})

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.core.serializers import serialize
from .models import Transaction
import json

@csrf_exempt  # Permite testes sem CSRF (remova em produção)
def transactions(request):
    if request.method == "GET":
        # Retorna todas as transações em JSON
        transactions = Transaction.objects.all().values()
        return JsonResponse(list(transactions), safe=False)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)  # Converte JSON para dicionário Python
            transaction = Transaction.objects.create(
                type=data["type"],
                amount=data["amount"],
                description=data["description"],
            )
            return JsonResponse({"message": "Transaction created!", "id": transaction.id}, status=201)
        except KeyError:
            return JsonResponse({"error": "Invalid data"}, status=400)

