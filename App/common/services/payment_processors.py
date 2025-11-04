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
    PDF 'Toolingo Bank' estilizado, sin libs externas. Incluye limpieza de acentos
    y símbolos para que el stream en latin-1 no se corrompa.
    """
    def __init__(self):
        self._pdf: Optional[bytes] = None
        self._filename: str = ""

    # ---------- helpers ----------
    def _esc(self, s: str) -> str:
        return (s or "").replace("(", r"\(").replace(")", r"\)")

    def _ascii(self, s: str) -> str:
        import unicodedata
        if s is None:
            return ""
        # translitera acentos -> ASCII (no “Ø”, “Æ”, “&n”, etc.)
        s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
        # evita caracteres de control y dobles espacios
        return " ".join(s.split())

    def process(self, *, user, total: int, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        total = _fmt_money(total)
        data = {
            "id": f"CHK-{int(now().timestamp())}-{uuid.uuid4().hex[:5].upper()}",
            "fecha_iso": now().isoformat(),
            "metodo": "cheque",
            "status": "approved",
            "total": total,
            "beneficiario": getattr(user, "get_full_name", lambda: "")() or getattr(user, "email", "") or "Usuario Toolingo",
            "extra": payload or {},
        }

        # ---------- medidas base ----------
        W, H = 595, 842      # A4
        M  = 64              # margen externo
        x0 = M
        CH = 280             # alto del cheque
        y0 = H - M - CH
        CW = W - 2*M

        # colores (0..1)
        brand = (0.976, 0.451, 0.086)  # #f97316
        ink   = (0.16, 0.20, 0.28)     # texto
        gray  = (0.70, 0.75, 0.80)     # líneas
        soft  = (0.45, 0.50, 0.58)     # labels

        def rgb_fill(c):     return f"{c[0]:.3f} {c[1]:.3f} {c[2]:.3f} rg"
        def rgb_stroke(c):   return f"{c[0]:.3f} {c[1]:.3f} {c[2]:.3f} RG"

        # ---------- estructura PDF ----------
        parts = []
        parts.append(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        parts.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
        parts.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
        # /F1 Helvetica, /F2 Helvetica-Bold
        parts.append(
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >> endobj\n"
        )
        parts.append(b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
        parts.append(b"6 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> endobj\n")

        # ---------- comandos de dibujo ----------
        cmds = []

        # fondo blanco + borde
        cmds += [rgb_fill((1,1,1)), f"{x0} {y0} {CW} {CH} re", "f"]
        cmds += [rgb_stroke(gray), "1 w", f"{x0} {y0} {CW} {CH} re", "S"]

        # barra superior brand
        bar_h = 48
        cmds += [rgb_fill(brand), f"{x0} {y0+CH-bar_h} {CW} {bar_h} re", "f"]

        # título Toolingo Bank (bold)
        cmds += [
            "BT /F2 20 Tf 1 1 1 rg",
            f"{x0+18} {y0+CH-bar_h+14} Td ({self._esc('Toolingo Bank')}) Tj",
            "ET"
        ]
        # subtítulo
        cmds += [
            "BT /F1 12 Tf 1 1 1 rg",
            f"{x0+230} {y0+CH-bar_h+18} Td ({self._esc('Cheque simulado')}) Tj",
            "ET"
        ]

        # monto grande arriba derecha
        monto_str = f"${total:,}".replace(",", ".")
        cmds += [
            "BT /F2 18 Tf " + rgb_fill(ink),
            f"{x0+CW-150} {y0+CH-bar_h-20} Td ({self._esc(monto_str)}) Tj",
            "ET"
        ]

        # fecha más legible
        try:
            iso = data["fecha_iso"]
            fecha_pretty = self._ascii(str(iso).replace("T", " ")[:16])
        except Exception:
            fecha_pretty = self._ascii(data["fecha_iso"])

        # filas
        line_y = y0 + CH - bar_h - 28
        step   = 26

        def label(lbl, xx, yy):
            lbl = self._ascii(lbl)
            return ["BT /F1 10 Tf " + rgb_fill(soft), f"{xx} {yy} Td ({self._esc(lbl)}) Tj", "ET"]

        def value(val, xx, yy):
            val = self._ascii(val)
            return ["BT /F1 12 Tf " + rgb_fill(ink), f"{xx} {yy} Td ({self._esc(val)}) Tj", "ET"]

        def hline(xx, yy, w):
            return [rgb_stroke(gray), "0.8 w", f"{xx} {yy} {w} 0 re", "S"]

        # Cheque No. + Fecha
        cmds += label("Cheque No.:", x0+16, line_y)
        cmds += value(self._ascii(data["id"]), x0+16, line_y-14)

        cmds += label("Fecha:", x0+CW-240, line_y)
        cmds += value(fecha_pretty, x0+CW-240, line_y-14)

        # Beneficiario
        line_y -= step
        cmds += label("Paguese a la orden de:", x0+16, line_y)
        cmds += value(self._ascii(data["beneficiario"]), x0+16, line_y-14)
        cmds += hline(x0+16, line_y-18, CW-32)

        # Monto literal
        line_y -= step
        cmds += label("La cantidad de:", x0+16, line_y)
        cmds += value(self._ascii(monto_str), x0+16, line_y-14)
        cmds += hline(x0+16, line_y-18, CW-32)

        # Banco & Ciudad
        line_y -= step
        cmds += label("Banco:", x0+16, line_y)
        cmds += value("Toolingo Bank", x0+16, line_y-14)
        cmds += hline(x0+16, line_y-18, 300)

        cmds += label("Ciudad:", x0+320, line_y)
        cmds += value("Medellin (CO)", x0+320, line_y-14)   # sin acentos para PDF
        cmds += hline(x0+320, line_y-18, CW-336)

        # Memo
        line_y -= step
        cmds += label("Memo:", x0+16, line_y)
        memo_text = self._ascii("Uso academico - no valido como titulo valor")
        cmds += value(memo_text, x0+16, line_y-14)
        cmds += hline(x0+16, line_y-18, CW-32)

        # caja de firma
        firma_w, firma_h = 200, 52
        firma_x = x0 + CW - firma_w - 16
        firma_y = y0 + 24
        cmds += [
            rgb_stroke(gray), "0.8 w", f"{firma_x} {firma_y} {firma_w} {firma_h} re", "S",
            "BT /F1 10 Tf " + rgb_fill(soft),
            f"{firma_x + 82} {firma_y - 14} Td ({self._esc('Firma')}) Tj",
            "ET",
        ]

        # stream
        stream_bytes = ("\n".join(cmds)).encode("latin-1", "ignore")
        stream = (
            b"<< /Length " + str(len(stream_bytes)).encode() + b" >>\n"
            b"stream\n" + stream_bytes + b"\nendstream\n"
        )
        parts.append(b"4 0 obj " + stream + b"endobj\n")

        # xref
        offs, out = [], b""
        for p in parts: offs.append(len(out)); out += p
        xref = len(out)
        out += b"xref\n0 7\n0000000000 65535 f \n"
        for o in offs: out += f"{o:010d} 00000 n \n".encode()
        out += b"trailer << /Size 7 /Root 1 0 R >>\nstartxref\n" + str(xref).encode() + b"\n%%EOF"

        self._pdf = out
        self._filename = f"cheque_{data['id']}.pdf"
        return data

    def artifact(self) -> Optional[Tuple[str, str, bytes]]:
        if not self._pdf:
            return None
        return (self._filename, "application/pdf", self._pdf)
