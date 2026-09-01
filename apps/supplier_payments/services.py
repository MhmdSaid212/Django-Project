from apps.supplier_payments.repositories import SupplierPaymentRepository


class SupplierPaymentService:
    def __init__(self, repository: SupplierPaymentRepository | None = None):
        self.repository = repository or SupplierPaymentRepository()

    def list_items(self):
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
