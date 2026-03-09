from typing import List
from abc import abstractmethod

from domain.api_client import BaseClient
from domain.models import (
    FilterValue,
    SearchApiResponse, 
    BaseContext,
)

class ConversationalSearchClient(BaseClient):
    """Abstract client for conversational search APIs that expose filtered product search.

    Implementations must call the platform's search endpoint and return a ``FilteredSearchApiResponse``
    that reflects the provided filter detection results, selected filter DTOs, and requested page size.
    """
    def __init__(self, base_url: str):
        super().__init__(base_url)

    @abstractmethod
    def search(
            self, 
            context: BaseContext,
            term: str,
            filters: List[FilterValue], 
            page_size: int,
        ) -> SearchApiResponse:
        pass
