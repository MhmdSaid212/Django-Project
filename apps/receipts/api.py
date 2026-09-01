from core.responses import not_implemented

def get_receipt(request, **kwargs):
    return not_implemented("GET /api/receipts/<id>/ is not implemented yet. Owner: Dev 3.")

def receipt_for_payment(request, **kwargs):
    return not_implemented("GET /api/payments/<payment_id>/receipt/ is not implemented yet. Owner: Dev 3.")
