# App/common/interfaces/payments.py
from __future__ import annotations
from typing import Any, Dict, Optional, Tuple

class PaymentProcessor:
    """
    Interfaz DIP para procesadores de pago.
    Implementaciones deben sobrescribir process() y (opcionalmente) artifact().
    """
    def process(self, *, user, total: int, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise NotImplementedError

    def artifact(self) -> Optional[Tuple[str, str, bytes]]:
        """Opcional: devuelve (filename, mimetype, bytes)."""
        return None
