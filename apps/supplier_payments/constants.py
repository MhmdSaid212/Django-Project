from core.constants import PaymentMethod

FIELD_CLASS = "field"

METHOD_LABELS = {
    PaymentMethod.CASH.value: "Cash",
    PaymentMethod.BANK_TRANSFER.value: "Bank transfer",
    PaymentMethod.CARD.value: "Card",
    PaymentMethod.CHEQUE.value: "Cheque",
    PaymentMethod.ONLINE.value: "Online",
    PaymentMethod.OTHER.value: "Other",
}
METHOD_CHOICES = tuple(METHOD_LABELS.items())
ALLOWED_METHODS = set(METHOD_LABELS)
