from dataclasses import dataclass

@dataclass
class FilterDefinition:
    label:str
    code:str
    type:str
    description:str