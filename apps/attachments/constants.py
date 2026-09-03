from core.constants import AttachmentCategory, AttachmentEntityType

CATEGORY_LABELS = {
    AttachmentCategory.PASSPORT.value: "Passport",
    AttachmentCategory.CONTRACT.value: "Contract",
    AttachmentCategory.RECEIPT.value: "Receipt",
    AttachmentCategory.BOOKING_DOCUMENT.value: "Booking document",
    AttachmentCategory.OTHER.value: "Other",
}
CATEGORY_CHOICES = tuple(CATEGORY_LABELS.items())

ENTITY_LABELS = {
    AttachmentEntityType.CUSTOMERS.value: "Customer",
    AttachmentEntityType.SUPPLIERS.value: "Supplier",
    AttachmentEntityType.EXPENSES.value: "Expense",
    AttachmentEntityType.BOOKINGS.value: "Booking",
    AttachmentEntityType.INVOICES.value: "Invoice",
    AttachmentEntityType.PACKAGES.value: "Package",
    AttachmentEntityType.TOURS.value: "Tour",
}
ENTITY_CHOICES = tuple(ENTITY_LABELS.items())

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
