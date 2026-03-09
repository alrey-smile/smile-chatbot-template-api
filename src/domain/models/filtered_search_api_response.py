from typing import List

from domain.models import SearchResponseItem, SearchApiResponse, FilterDto

class FilteredSearchApiResponse(SearchApiResponse):
    def __init__(
            self, 
            total_count:int,
            items:List[SearchResponseItem],
            aggregations:List[FilterDto],
            code:int,
            filter_name:str,
            is_filter_included:bool,
            message:str = "", 
            query:str = ""):
        super().__init__(
            total_count=total_count, 
            items=items, 
            aggregations=aggregations,
            code=code,
            message=message, 
            query=query
        )
        self.filter_name=filter_name
        self.is_filter_included=is_filter_included

    def build_from_search_api_response(response:SearchApiResponse, filter_name:str, is_filter_included:bool):
        return FilteredSearchApiResponse(
            total_count=response.total_count,
            items=response.items,
            aggregations=response.aggregations,
            code=response.code,
            message=response.message,
            query=response.query,
            filter_name=filter_name,
            is_filter_included=is_filter_included
        )