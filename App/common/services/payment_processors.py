# App/common/services/payment_processors.py
from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
from django.utils.timezone import now
import uuid
from common.interfaces.payments import PaymentProcessor

def _fmt_money(v: int) -> int:
    return int(v or 0)

class WalletPaymentProcessor(PaymentProcessor):
    """
    Resta del saldo del usuario si existe perfil.saldo; si no, usa sesión (wallet demo).
    """
    def __init__(self, request):
        self.request = request

    def _get_wallet(self, user) -> int:
        perfil = getattr(user, "profile", None) or getattr(user, "perfil", None)
        if perfil is not None and hasattr(perfil, "saldo"):
            try:
                return int(getattr(perfil, "saldo") or 0)
            except Exception:
                return 0
        # saldo demo en sesión
        try:
            return int(self.request.session.get("wallet_saldo", 500_000))
        except Exception:
            return 0

    def _save_wallet(self, user, new_value: int) -> None:
        perfil = getattr(user, "profile", None) or getattr(user, "perfil", None)
        if perfil is not None and hasattr(perfil, "saldo"):
            setattr(perfil, "saldo", int(new_value))
            perfil.save(update_fields=["saldo"])
            return
        self.request.session["wallet_saldo"] = int(new_value)

    def process(self, *, user, total: int, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        total = _fmt_money(total)
        wallet_before = self._get_wallet(user)
        if wallet_before < total:
            return {
                "status": "rejected",
                "error": "Fondos insuficientes en la billetera.",
                "wallet_before": wallet_before,
                "required": total,
            }
        wallet_after = wallet_before - total
        self._save_wallet(user, wallet_after)

        pay_id = f"WAL-{int(now().timestamp())}-{uuid.uuid4().hex[:6].upper()}"
        return {
            "id": pay_id,
            "fecha_iso": now().isoformat(),
            "metodo": "wallet",
            "status": "approved",
            "total": total,
            "wallet_before": wallet_before,
            "wallet_after": wallet_after,
            "extra": payload or {},
        }

class ChequePdfPaymentProcessor(PaymentProcessor):
    """
    Genera un PDF mínimo con los datos del cheque (sin librerías externas).
    """
    def __init__(self):
        self._pdf: Optional[bytes] = None
        self._filename: str = ""

    def process(self, *, user, total: int, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        total = _fmt_money(total)
        beneficiario = ""
        try:
            beneficiario = user.get_full_name() or ""
        except Exception:
            beneficiario = ""
        if not beneficiario:
            beneficiario = getattr(user, "email", "") or "Usuario Toolingo"

        data = {
            "id": f"CHK-{int(now().timestamp())}-{uuid.uuid4().hex[:6].upper()}",
            "fecha_iso": now().isoformat(),
            "metodo": "cheque",
            "status": "approved",
            "total": total,
            "beneficiario": beneficiario,
            "extra": payload or {},
        }

        # Construcción PDF (ASCII seguro para latin-1)
        lines = [
            "Toolingo - Cheque simulado",
            f"ID: {data['id']}",
            f"Fecha: {data['fecha_iso']}",
            f"Beneficiario: {data['beneficiario']}",
            f"Total: ${total:,}".replace(",", "."),
            "Banco: Toolingo Bank",
            "Ciudad: Medellin (CO)",
            "Uso academico - no valido como titulo valor",
        ]

        parts: list[bytes] = []
        parts.append(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        parts.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
        parts.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
        parts.append(b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n")
        parts.append(b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")

        cmds = ["BT /F1 12 Tf 0 0 0 rg"]
        y = 770
        for ln in lines:
            ln = ln.replace("(", r"\(").replace(")", r"\)")
            cmds.append(f"72 {y} Td ({ln}) Tj")
            y -= 16
        cmds.append("ET")
        stream_text = "\n".join(cmds).encode("latin-1")
        stream = (
            b"<< /Length " + str(len(stream_text)).encode() + b" >>\n"
            b"stream\n" + stream_text + b"\nendstream\n"
        )
        parts.append(b"4 0 obj " + stream + b"endobj\n")

        xref_pos: list[int] = []
        out = b""
        for p in parts:
            xref_pos.append(len(out))
            out += p
        xref_start = len(out)
        out += b"xref\n0 6\n0000000000 65535 f \n"
        for pos in xref_pos:
            out += f"{pos:010d} 00000 n \n".encode()
        out += b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n" + str(xref_start).encode() + b"\n%%EOF"

        self._pdf = out
        self._filename = f"cheque_{data['id']}.pdf"
        return data

    def artifact(self) -> Optional[Tuple[str, str, bytes]]:
        if not self._pdf:
            return None
        return (self._filename, "application/pdf", self._pdf)
