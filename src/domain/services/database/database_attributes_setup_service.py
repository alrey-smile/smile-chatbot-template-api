from typing import List
from abc import ABC, abstractmethod

from domain.models import AttributeSetDto, AttributeFilterDto, FilterDto

class DatabaseAttributesSetupService(ABC):
    """Contract for persisting attribute sets and their filters.

    Implementations are responsible for storing attribute set definitions,
    fetching them by identifier or name, and managing the filters associated
    with each set so that the chatbot can bootstrap its database metadata.
    """

    @abstractmethod
    def insert_attribute_set(self, attribute_set:AttributeSetDto):
        """Persist a new attribute set definition."""
        pass

    @abstractmethod
    def get_attribute_set(self, attribute_set_id:int) -> AttributeSetDto:
        """Return the attribute set identified by `attribute_set_id`."""
        pass
    
    @abstractmethod
    def get_attribute_set_by_name(self, attribute_set_name:str) -> AttributeSetDto:
        """Return the attribute set whose name matches `attribute_set_name`."""
        pass

    @abstractmethod
    def load_attribute_sets(self) -> List[AttributeSetDto]:
        """Return every attribute set currently stored in the database."""
        pass

    @abstractmethod
    def insert_filters(self, attribute_set_id:int, filters:List[AttributeFilterDto]): 
        """Persist the provided `filters` for the attribute set `attribute_set_id`."""
        pass
    
    @abstractmethod
    def get_filters(self, attribute_set_id:int) -> List[AttributeFilterDto]:
        """Return the filters associated with `attribute_set_id`."""
        pass
    
    @abstractmethod
    def get_all_filters(self) -> List[FilterDto]:
        """Return the filters associated with `attribute_set_id`."""
        pass