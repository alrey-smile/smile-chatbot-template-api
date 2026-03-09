from dataclasses import dataclass, field
from typing import List, Any

from domain.models.filter_definition import FilterDefinition

@dataclass
class FilterDto(FilterDefinition):
    options_type: str = ""
    options: List[Any] = field(default_factory=list)
    
    def from_dto(dto: dict):
        return FilterDto(
            label=dto.get("label"),
            code=dto.get("code"),
            type=dto.get("type"),
            description=dto.get("description"),
            options_type=dto.get("options_type", ""),
            options=dto.get("options", []),
        )