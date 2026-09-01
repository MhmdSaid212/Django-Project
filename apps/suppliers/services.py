from apps.suppliers.repositories import SupplierRepository


class SupplierService:
    def __init__(self, repository: SupplierRepository | None = None):
        self.repository = repository or SupplierRepository()

    def list_items(self):
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
