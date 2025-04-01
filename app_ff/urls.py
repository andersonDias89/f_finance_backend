from django.urls import path
from .views import hello_world
from .views import transactions


urlpatterns = [
    path('hello/', hello_world),  # Essa rota será acessível em /hello/
    path("transactions/", transactions, name="transactions")
]