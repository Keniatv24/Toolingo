from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.views import APIView
from common.services.payment_factory import make_processor


def pagos_view(request):
    
    return render(request, "checkout/pagos.html")

class NotificacionesList(APIView):
    """
    Stub de notificaciones para no romper el detalle.
    Retorna una lista vacía (ajústalo luego a tu lógica real).
    """
    permission_classes = [permissions.IsAuthenticated]  

    def get(self, request):
        return Response([])
    
class SimularPagoView(APIView):
    """
    POST /api/pagos/simular/
    Body:
      { "metodo":"wallet"|"cheque", "total":165000, "payload":{...} }
    Query opcional:
      ?artefacto=1  -> si metodo=cheque, devuelve PDF.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data or {}
        metodo = (data.get("metodo") or "wallet").lower()
        try:
            total = int(data.get("total") or 0)
        except Exception:
            return Response({"detail":"total inválido"}, status=status.HTTP_400_BAD_REQUEST)
        if total <= 0:
            return Response({"detail":"total inválido"}, status=status.HTTP_400_BAD_REQUEST)

        payload = data.get("payload") or {}
        proc = make_processor(metodo, request=request)
        result = proc.process(user=request.user, total=total, payload=payload)

        # Si pidieron artefacto (PDF de cheque) lo devolvemos como attachment
        want_art = str(request.query_params.get("artefacto", "0")).lower() in ("1","true","yes","si","sí")
        art = proc.artifact() if want_art else None
        if art:
            filename, mimetype, content = art
            from django.http import HttpResponse
            resp = HttpResponse(content, content_type=mimetype)
            resp["Content-Disposition"] = f'attachment; filename="{filename}"'
            return resp

        return Response(result, status=status.HTTP_200_OK)