import json
import re
from pathlib import Path
from typing import Annotated, List, Optional
from fastapi import Depends
from urllib.parse import urlparse, urlunparse

from domain.models import (
    FilteredSearchApiResponse,
    SearchApiResponse, 
    AttributeFilterValue, 
    ProductFilterDetectionResult, 
    AttributeFilterDto,
    SearchContext
)
from domain.fields import PriceRangeField
from domain.api_client import ConversationalSearchClient
from domain.logger import ContextLogger
from infrastructure.search.elastic_suite import (
    ElasticSuiteSearchResponseBuilder, 
    OneFilterSelectionStrategy,
    ElasticSuiteGraphqlQueryFactory
)
from config import Settings, get_settings

class ElasticSuiteSearchClientMock(ConversationalSearchClient):
    def __init__(
        self,
        settings: Annotated[Settings, Depends(get_settings)],
        search_response_builder: Annotated[ElasticSuiteSearchResponseBuilder, Depends(ElasticSuiteSearchResponseBuilder)],
        logger: Annotated[ContextLogger, Depends(ContextLogger)],
    ):
        super().__init__(settings.elastic_suite_search_api_base_url)
        self.settings = settings
        self.search_response_builder = search_response_builder
        self.logger = logger
        self.graphql_factory = ElasticSuiteGraphqlQueryFactory()
        self._mock_search_response: Optional[SearchApiResponse] = None

    def search(self, 
            filter_detection_result:ProductFilterDetectionResult,
            filters_dto:List[AttributeFilterDto],
            context:SearchContext,
            page_size: int = 10) -> FilteredSearchApiResponse:
        if self._mock_search_response is None:
            base_path = Path(__file__).resolve()
            for parent in base_path.parents:
                candidate = parent / "data" / "search_response_23.json"
                if candidate.exists():
                    mock_file = candidate
                    break
            else:
                raise FileNotFoundError("Cannot locate mock search response at data/search_response_23.json.")
            with mock_file.open(encoding="utf-8") as response_file:
                response_data = json.load(response_file)
            self._mock_search_response = self.search_response_builder.build_from_api_response(response_data)

        context.search_used_filters = []
        context.search_used_filters = [
            AttributeFilterValue(
                attribute_id=2545,
                label="Price",
                code="price",
                type="price",
                description="",
                value=PriceRangeField(min_price=0, max_price=300)
            ),
            AttributeFilterValue(
                attribute_id=2545,
                label="Marque",
                code="marque",
                type="text",
                description="", 
                value="WEBER"
            ),
            AttributeFilterValue(
                attribute_id=2545,
                label="Type de produit",
                code="type_produit",
                type="text",
                description="",
                value="Barbecue"
            ),
            # AttributeFilterValue(
            #     attribute_id=2545,
            #     label="Couleur",
            #     code="couleur",
            #     type="text",
            #     description="",
            #     value="Noir"
            # )
        ]
        return FilteredSearchApiResponse.build_from_search_api_response(
            response=self._mock_search_response,
            filter_name=None,
            is_filter_included=False
        )
