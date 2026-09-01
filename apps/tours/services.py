from apps.tours.repositories import TourRepository


class TourService:
    def __init__(self, repository: TourRepository | None = None):
        self.repository = repository or TourRepository()

    def list_items(self):
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
