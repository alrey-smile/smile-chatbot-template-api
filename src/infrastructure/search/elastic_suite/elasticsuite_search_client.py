import json
import re
from typing import Annotated, List
from fastapi import Depends
from urllib.parse import urlparse, urlunparse

from domain.models import (
    FilteredSearchApiResponse,
    SearchApiResponse, 
    FilterValue,
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

class ElasticSuiteSearchClient(ConversationalSearchClient):
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
        self.url = self.__insert_credentials(
            url=self.api_base_url,
            credentials=self.settings.elastic_suite_search_api_credentials,
        )
        (x_correlation_id_key, x_correlation_id_value) = self.create_x_correlation_id()
        (content_type_key, content_type_value) = self.create_json_content_type()
        self.headers = {
            x_correlation_id_key: x_correlation_id_value,
            content_type_key: content_type_value,
            "Store": settings.elasticsuite_magento_store_code
        }
        self.graphql_factory = ElasticSuiteGraphqlQueryFactory()

    def search(
            self, 
            context:SearchContext,
            term:str,
            filters:List[FilterValue], 
            page_size: int = 10
        ) -> FilteredSearchApiResponse:

        # Searching only with 'term'
        if not filters:
            response = self._do_search(
                context,
                term,
                [],
                page_size)
            context.search_used_filters = []
            return FilteredSearchApiResponse.build_from_search_api_response(
                response=response,
                filter_name=None,
                is_filter_included=False
            )
        
        # Search with all
        response = self._do_search(
            context,
            term,
            filters,
            page_size)
        
        # TODO: manage search error (no total_count)
        if response.total_count > 0:
            context.search_used_filters = filters
            return FilteredSearchApiResponse.build_from_search_api_response(
                response=response,
                filter_name=None,
                is_filter_included=False
            )
        
        best_response = None
        best_score = -1

        filter_selection_strategy = OneFilterSelectionStrategy(filters)
        search_selected_filters = []
        
        while filter_selection_strategy.has_next():
            not_selected_filters, selected_filters = filter_selection_strategy.next() # invert result so we want all the rest filters
            response = self._do_search(
                context,
                term,
                selected_filters,
                page_size)
            score = response.total_count
            if (best_response is None or score > best_score) and response.total_count > 0:
                best_response = FilteredSearchApiResponse.build_from_search_api_response(
                    response=response,
                    filter_name=not_selected_filters[0].label,
                    is_filter_included=False
                )
                best_score = score
                search_selected_filters = selected_filters
        
        if best_score > 0:
            context.search_used_filters = search_selected_filters
            return best_response
        
        filter_selection_strategy.reset()

        while filter_selection_strategy.has_next():
            selected_filters, _ = filter_selection_strategy.next()
            response = self._do_search(
                context,
                term,
                selected_filters,
                page_size)
            score = response.total_count
            if (best_response is None or score > best_score) and response.total_count > 0:
                best_response = FilteredSearchApiResponse.build_from_search_api_response(
                    response=response,
                    filter_name=selected_filters[0].label,
                    is_filter_included=True
                )
                best_score = score
                search_selected_filters = selected_filters
        
        if best_score <= 0:
            response = self._do_search(
                context,
                term,
                [],
                page_size)
            context.search_used_filters = []
            return FilteredSearchApiResponse.build_from_search_api_response(
                response=response,
                filter_name=None,
                is_filter_included=False
            )
        else:
            context.search_used_filters = search_selected_filters
            return best_response

    def _do_search(
        self,
        context:SearchContext,
        search_term:str, 
        filters:List[FilterValue],
        page_size: int = 10) -> SearchApiResponse:

        json_data = self.graphql_factory.build_data(
            search_term=search_term,
            filters=filters, 
            page_size=page_size
        )

        # Log a compact, single-line payload
        log_payload = {
            "query": re.sub(r"\s+", " ", json_data["query"]).strip(),
            "variables": json_data["variables"],
        }
        self.logger.debug_context(message=json.dumps(log_payload, ensure_ascii=False), context=context)

        response = self.post(url=self.url, headers=self.headers, json_data=json_data)
        return self.search_response_builder.build_response(response)
        
    def __insert_credentials(self, url: str, credentials: str) -> str:
        parsed = urlparse(url)
        netloc = f"{credentials}@{parsed.hostname}" + (f":{parsed.port}" if parsed.port else "")
        return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))