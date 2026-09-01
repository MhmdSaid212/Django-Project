from apps.packages.repositories import PackageRepository


class PackageService:
    def __init__(self, repository: PackageRepository | None = None):
        self.repository = repository or PackageRepository()

    def list_items(self):
        return self.repository.find_all()

    def get(self, doc_id: str):
        return self.repository.find_by_id(doc_id)
