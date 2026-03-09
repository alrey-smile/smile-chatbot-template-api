from typing import Any
from dataclasses import dataclass, field

from domain.models import FilterDto

@dataclass
class FilterValue(FilterDto):
    value: Any = field(default=None)  # str or PriceRange