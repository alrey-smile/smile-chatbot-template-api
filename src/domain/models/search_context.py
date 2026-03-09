from typing import List
from dataclasses import dataclass, field

from domain.fields import AttributeSetField
from domain.models import (
    UserRequestDto,
    AttributeSetDto,
    ProductFilterDetectionResult,
    SearchResponseItem,
    Language,
    BaseContext,
    FilterValue,
    FilterDto
)

@dataclass
class SearchContext(BaseContext):
    search_lang: Language = None
    search_term: str = ""
    search_used_filters: List[FilterValue] = field(default_factory=list)
    requests: List[UserRequestDto] = field(default_factory=list)
    request_chain_results: List[ProductFilterDetectionResult] = field(default_factory=list)
    search_result:List[SearchResponseItem] = field(default_factory=list)
    search_total_count:int = 0
    search_available_filters: List[FilterDto] = field(default_factory=list)
    max_products: int = 10
    needs_reset: bool = False

    # Deprecated fields
    attribute_sets: List[AttributeSetDto] = field(default_factory=list)
    detected_attribute_set: AttributeSetField = None

    def get_valued_filters(self):
        return [f for f in self.request_chain_results[0].detected_filters if self.__is_valued(f.value)]
    
    def __is_valued(self, filter_value):
        if isinstance(filter_value, dict):
            # handle case where PriceRangeField is represented as dict
            min_price = filter_value.get("min_price") or 0
            max_price = filter_value.get("max_price") or 0
            return max_price > 0 or min_price > 0
        else:
            return True if filter_value else False