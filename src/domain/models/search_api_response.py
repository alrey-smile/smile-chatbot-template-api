from typing import List

from domain.models.search_response_item import SearchResponseItem
from domain.models.api_response import ApiResponse
from domain.models.filter_dto import FilterDto

class SearchApiResponse(ApiResponse):
    def __init__(
            self, 
            total_count:int,
            items:List[SearchResponseItem], 
            aggregations:List[FilterDto],
            code:int, 
            message:str = "", 
            query:str = ""):
        super().__init__(code=code, message=message, query=query)
        self.total_count = total_count
        self.items = items
        self.aggregations = aggregations
