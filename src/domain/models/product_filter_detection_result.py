from typing import List
from dataclasses import dataclass

from domain.models import FilterValue

@dataclass
class ProductFilterDetectionResult:
    search_term:str
    ai_question:str
    detected_filters:List[FilterValue]