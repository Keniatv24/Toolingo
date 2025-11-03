# App/common/services/payment_factory.py
from __future__ import annotations
from typing import Any
from common.services.payment_processors import (
    WalletPaymentProcessor,
    ChequePdfPaymentProcessor,
)

def make_processor(kind: str, *, request: Any = None):
    """
    Fábrica DIP: según el 'kind' retorna la implementación concreta.
    """
    k = (kind or "").lower().strip()
    if k == "cheque":
        return ChequePdfPaymentProcessor()
    # default -> wallet
    return WalletPaymentProcessor(request=request)
