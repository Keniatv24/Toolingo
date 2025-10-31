from django.shortcuts import render

def pagos_view(request):
    
    return render(request, "checkout/pagos.html")