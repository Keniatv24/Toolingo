# App/App/views.py
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.timezone import now
from datetime import timedelta

from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.views import APIView

from common.services.payment_factory import make_processor
from rentals.models import CartItem, Alquiler

# ---------------- PÁGINAS ----------------
def pagos_view(request):
    return render(request, "checkout/pagos.html")


# ---------------- NOTIFICACIONES (en sesión) ----------------
def _notif_box(request):
    """
    Bandeja de notificaciones guardada en sesión por usuario.
    Estructura de cada notificación:
    {
      "id": "rev-<articulo_id>-<ts>",
      "kind": "review_request",
      "title": "...",
      "body": "...",
      "action_url": "/articulo/<id>/#opiniones",
      "created_at": iso,
      "expires_at": iso | None,
      "read_at": iso | None
    }
    """
    request.session.setdefault("notifs", [])
    return request.session["notifs"]


class NotificacionesList(APIView):
    """GET /api/notificaciones/ -> lista activas"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        box = _notif_box(request)
        alive = []
        tnow = now()
        for n in box:
            if n.get("read_at"):
                continue
            exp = n.get("expires_at")
            if exp and tnow.isoformat() > exp:
                continue
            alive.append(n)
        request.session["notifs"] = box
        request.session.modified = True
        return Response({"count": len(alive), "results": alive})


class NotificacionesMarkAll(APIView):
    """POST /api/notificaciones/marcar-todas/ -> marca leídas"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        box = _notif_box(request)
        tnow = now().isoformat()
        marked = 0
        for n in box:
            if not n.get("read_at"):
                n["read_at"] = tnow
                marked += 1
        request.session["notifs"] = box
        request.session.modified = True
        return Response({"marked": marked}, status=status.HTTP_204_NO_CONTENT)


# ---------------- WALLET (lo que te estaba faltando) ----------------
class WalletBalanceView(APIView):
    """
    GET /api/wallet/saldo/ -> { "saldo": int }
    Lee de perfil.saldo si existe; si no, usa sesión (demo).
    """
    permission_classes = [permissions.IsAuthenticated]

    def _get_wallet(self, request):
        user = request.user
        perfil = getattr(user, "profile", None) or getattr(user, "perfil", None)
        if perfil is not None and hasattr(perfil, "saldo"):
            return int(getattr(perfil, "saldo") or 0), "profile"
        return int(request.session.get("wallet_saldo", 1_000_000)), "session"

    def _set_wallet(self, request, value, where):
        if where == "profile":
            perfil = getattr(request.user, "profile", None) or getattr(request.user, "perfil", None)
            if perfil is not None and hasattr(perfil, "saldo"):
                setattr(perfil, "saldo", int(value))
                perfil.save(update_fields=["saldo"])
                return
        request.session["wallet_saldo"] = int(value)
        request.session.modified = True

    def get(self, request):
        saldo, _ = self._get_wallet(request)
        return Response({"saldo": int(saldo)})


class WalletRechargeView(APIView):
    """
    POST /api/wallet/recargar/ { "monto": 200000 } -> { "saldo": new_value }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            monto = int(request.data.get("monto") or 0)
        except Exception:
            return Response({"detail": "monto inválido"}, status=status.HTTP_400_BAD_REQUEST)
        if monto <= 0:
            return Response({"detail": "monto inválido"}, status=status.HTTP_400_BAD_REQUEST)

        bal_view = WalletBalanceView()
        saldo, where = bal_view._get_wallet(request)
        new_value = saldo + monto
        bal_view._set_wallet(request, new_value, where)
        return Response({"saldo": new_value})


# ---------------- PAGO / SIMULACIÓN ----------------
COMPLETED_STATES = {"FINALIZADO", "FINALIZADA", "COMPLETADO", "CERRADO", "TERMINADO"}

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
            return Response({"detail": "total inválido"}, status=status.HTTP_400_BAD_REQUEST)
        if total <= 0:
            return Response({"detail": "total inválido"}, status=status.HTTP_400_BAD_REQUEST)

        payload = data.get("payload") or {}
        proc = make_processor(metodo, request=request)
        result = proc.process(user=request.user, total=total, payload=payload)

        # Si mandan alquiler_id en payload, cerramos el alquiler tras pagar
        alquiler_id = payload.get("alquiler_id")
        if alquiler_id:
            try:
                a = Alquiler.objects.get(id=alquiler_id, arrendatario=request.user)
                if a.estado not in COMPLETED_STATES:
                    a.estado = "FINALIZADO"
                    a.save(update_fields=["estado"])
            except Alquiler.DoesNotExist:
                pass

        # Si pidieron artefacto (PDF de cheque), devolver attachment
        want_art = str(request.query_params.get("artefacto", "0")).lower() in ("1", "true", "yes", "si", "sí")
        art = proc.artifact() if want_art else None
        if art:
            filename, mimetype, content = art
            resp = HttpResponse(content, content_type=mimetype)
            resp["Content-Disposition"] = f'attachment; filename="{filename}"'
            return resp

        # Notificación “Califica el artículo…”
        try:
            items = CartItem.objects.filter(user=request.user).select_related("articulo")
            box = _notif_box(request)
            tnow = now()
            for it in items:
                art_obj = getattr(it, "articulo", None)
                if not art_obj:
                    continue
                box.append({
                    "id": f"rev-{art_obj.id}-{int(tnow.timestamp())}",
                    "kind": "review_request",
                    "title": "Califica el artículo que adquiriste",
                    "body": f"Cuéntanos cómo te fue con “{getattr(art_obj, 'titulo', str(art_obj.id))}”.",
                    "action_url": f"/articulo/{art_obj.id}/#opiniones",
                    "created_at": tnow.isoformat(),
                    "expires_at": (tnow + timedelta(days=5)).isoformat(),
                    "read_at": None,
                })
            request.session["notifs"] = box
            request.session.modified = True
        except Exception:
            pass

        return Response(result, status=status.HTTP_200_OK)
