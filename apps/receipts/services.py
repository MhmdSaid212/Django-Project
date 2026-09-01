from apps.receipts.repositories import ReceiptRepository


class ReceiptService:
    def __init__(self, repository: ReceiptRepository | None = None):
        self.repository = repository or ReceiptRepository()

    def list_items(self):
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
