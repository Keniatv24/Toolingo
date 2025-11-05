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
    
class WalletBalanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_wallet(self, request):
        user = request.user
        perfil = getattr(user, "profile", None) or getattr(user, "perfil", None)
        if perfil is not None and hasattr(perfil, "saldo"):
            return int(getattr(perfil, "saldo") or 0), "profile"
        return int(request.session.get("wallet_saldo", 1_000_000)), "session"

    def set_wallet(self, request, value, where):
        if where == "profile":
            perfil = getattr(request.user, "profile", None) or getattr(request.user, "perfil", None)
            if perfil is not None and hasattr(perfil, "saldo"):
                setattr(perfil, "saldo", int(value))
                perfil.save(update_fields=["saldo"])
                return
        request.session["wallet_saldo"] = int(value)

    def get(self, request):
        saldo, _ = self.get_wallet(request)
        return Response({"saldo": int(saldo)})

class WalletRechargeView(APIView):
    """
    Demo de recarga de saldo para la billetera.
    POST /api/wallet/recargar/ { "monto": 200000 }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            monto = int(request.data.get("monto") or 0)
        except Exception:
            return Response({"detail":"monto inválido"}, status=status.HTTP_400_BAD_REQUEST)
        if monto <= 0:
            return Response({"detail":"monto inválido"}, status=status.HTTP_400_BAD_REQUEST)

        bal_view = WalletBalanceView()
        saldo, where = bal_view.get_wallet(request)
        new_value = saldo + monto
        bal_view.set_wallet(request, new_value, where)
        return Response({"saldo": new_value})