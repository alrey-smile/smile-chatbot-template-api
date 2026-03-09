from typing import Annotated, Tuple
from fastapi import Depends

from domain.models import SearchContext, FilteredSearchApiResponse, FilterDto
from domain.api_client import ConversationalSearchClient
from domain.logger import ContextLogger

from application.agents import QuestionsSummarizerAgent, SearchResponseBuilderAgent, SearchTermExtractionAgent

from dependencies import (
    inject_conversational_search_api, 
    inject_logger, 
    inject_search_response_agent,
)

class SearchManager:
    """Coordinates conversational product search by invoking summarization, retrieval, and response agents."""

    def __init__(
            self,
            summarize_question_agent : Annotated[QuestionsSummarizerAgent, Depends(QuestionsSummarizerAgent)],
            search_term_extraction_agent: Annotated[SearchTermExtractionAgent, Depends(SearchTermExtractionAgent)],
            search_response_agent: Annotated[SearchResponseBuilderAgent, Depends(inject_search_response_agent)],
            conversational_search_client: Annotated[ConversationalSearchClient, Depends(inject_conversational_search_api)],
            logger: Annotated[ContextLogger, Depends(inject_logger)]):
        """Store injected dependencies used to prepare and execute conversational search queries."""
        self.summarize_question_agent = summarize_question_agent
        self.search_term_extraction_agent = search_term_extraction_agent
        self.conversational_search_client = conversational_search_client
        self.search_response_agent = search_response_agent
        self.logger = logger

    def extract_search_term(self, context: SearchContext) -> SearchContext:
        """Extract search term and detect if it's a new search.
        
        Returns:
            Updated context with search_term and needs_reset flag set.
        """
        search_term, is_new_search = self.search_term_extraction_agent.invoke(context)
        context.needs_reset = not context.is_first_call and is_new_search
        context.search_term = search_term
        return context

    def search(self, context: SearchContext) -> SearchContext:
        """Execute the conversational search flow and enrich the provided context with results.

        Args:
            context: Carries conversation history, filter hypotheses, and required attribute sets.

        Returns:
            The same context instance updated with `ai_answer` and `search_result`.

        Raises:
            KeyError: When an attribute set referenced by a filter hypothesis is missing.
        """

        # no_question =  all([not request.ai_question.strip() for request in context.request_chain_results])
        # too_many_questions = any([message.type == "ai" for message in context.message_thread])

        #if no_question or too_many_questions:
        total_count = 0
        
        # Launch the search (/!\ Only one product search hypothesis)
        items = []
        api_response: FilteredSearchApiResponse = None
        aggregations_dict: dict[str, FilterDto] = {}
        
        for dectected_chain in context.request_chain_results:
            api_response = self.conversational_search_client.search(
                term=dectected_chain.search_term,
                filters=dectected_chain.detected_filters,
                context=context,
                page_size=context.max_products
            )
            if api_response.code == 200:
                items.extend(api_response.items)
                total_count += api_response.total_count
                for agg in api_response.aggregations:
                    if agg.code not in aggregations_dict:
                        aggregations_dict[agg.code] = agg
            else:
                self.logger.info_context(api_response.message, context)

            # Create an answer calling to the right agent (no products, or products)

        context.search_total_count = total_count
        context.search_result = items
        context.search_available_filters = list(aggregations_dict.values())
        
        # for response_strategy in self.search_response_agent_strategies:
        #     if response_strategy.apply(context):
        #         answer = response_strategy.invoke(context)
        #         context.ai_answer = answer                
        #         break

        if len(items) == 0:
            empty_search_answer = self.search_response_agent.invoke_empty(context)
            context.ai_answer = empty_search_answer
            context.search_result = []
        
        else:
            not_empty_search_answer = self.search_response_agent.invoke_not_empty(context=context)
            context.ai_answer = not_empty_search_answer
            context.search_result = items
            
            # TODO: take into account all the result for the answer

        # else:
        #     # Summarize the set of questions
        #     summarized_question = self.summarize_question_agent.invoke(context)
        #     context.ai_answer = summarized_question
        #     context.search_result = []
        
        return context