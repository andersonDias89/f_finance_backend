from django.http import JsonResponse

def hello_world(request):
    """
    A simple view that returns a JSON response with a greeting message.
    """
    return JsonResponse({'message': 'Hello, world!'})
