from requests import Response
from typing import List

from domain.api_client import ApiResponseBuilder
from domain.models import SearchApiResponse, ApiResponse, SearchResponseItem, FilterDto

class ElasticSuiteSearchResponseBuilder(ApiResponseBuilder):
    def __init__(self):
        super().__init__("We can't find products with your criteria.")

    def build_response(self, response: Response) -> SearchApiResponse:

        if response.status_code == 200 and 'error' not in response.json():
            responseData = response.json()
            if not isinstance(responseData, list) or 'error' not in responseData[0]:
                return self.build_from_api_response(response.json())
        
        error_message = self.messages.get(response.status_code, "Unknown error.")
        return SearchApiResponse(   
            code=response.status_code, 
            message=error_message,
            query="",
            items=[],
            total_count=0
        )

    def build_from_api_response(self, response:dict) -> SearchApiResponse:
        if response and "data" in response:
            product = response["data"]["products"]
            total_count = product["total_count"] 
            items:List[SearchResponseItem] = []
            aggregations:List[FilterDto] = []
            for item in product["items"]:
                items.append(self._build_search_result_from_response(item))
            for aggregation in product["aggregations"]:
                aggregations.append(self._build_search_filter_from_response(aggregation))
            return SearchApiResponse(
                code=200,
                message="Success",
                query="",
                items=items,
                total_count=total_count,
                aggregations=aggregations,
            )
        else:
            return ApiResponse(
                code=500,
                message="We encounter a problem during external search.",
                query=""
            )
        
    def _build_search_result_from_response(self, item:dict) -> SearchResponseItem:
        price_info = item["price_range"]["minimum_price"]["final_price"]
        value = price_info["value"]
        currency = price_info["currency"]
        price = f"{value} {currency}"
        return SearchResponseItem(
            id=item["id"],
            sku=item["sku"],
            name=item["name"],
            price=price,
            image_url=item["image"]["url"],
            url_key=item["url_key"]
        )
            
    def _build_search_filter_from_response(self, aggregation:dict) -> FilterDto:
        return FilterDto(
            code=aggregation["attribute_code"],
            label=aggregation["label"],
            description="",
            type=aggregation["frontend_input"],
            options=[option["label"] for option in aggregation["options"]],
            options_type="str",
        )