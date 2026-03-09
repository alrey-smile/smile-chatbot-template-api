from typing import Annotated, Tuple
from fastapi import Depends

from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from domain.models import SearchContext
from domain.ai import LlmProvider
from domain.fields import SearchTermField

from application.prompts import PromptProvider

from dependencies import inject_deep_llm_provider, inject_search_term_extraction_prompt
from config import Settings, get_settings

class SearchTermExtractionAgent:
    """Extract the main search term from a user message, independent of attribute sets."""

    def __init__(self, 
            settings: Annotated[Settings, Depends(get_settings)], 
            llm_agent: Annotated[LlmProvider, Depends(inject_deep_llm_provider)],
            prompt_provider: Annotated[PromptProvider[SearchContext], Depends(inject_search_term_extraction_prompt)]):
        """Store injected dependencies for search term extraction."""
        self.settings = settings
        self.llm_agent = llm_agent
        self.prompt_provider = prompt_provider
        self.pydantic_object = SearchTermField

    def invoke(self, context: SearchContext) -> Tuple[str, bool]:
        """Extract search term and detect if it's a new search.
        
        Returns:
            Tuple of (search_term, is_new_search)
        """
        output_parser = PydanticOutputParser(pydantic_object=self.pydantic_object)
        format_instructions = output_parser.get_format_instructions()
        prompt_template: ChatPromptTemplate = self.prompt_provider.get_prompt(context)

        previous_search_term = self._get_previous_search_term(context)
        prompt_template = prompt_template.partial(
            format_instructions=format_instructions,
            previous_search_term=previous_search_term
        )
        messages = prompt_template.format_messages(question=context.exchange)
        output = self.llm_agent.invoke(messages)

        response = output_parser.parse(output.content)
        return response.term, response.is_new_search

    def _get_previous_search_term(self, context: SearchContext) -> str:
        """Extract the previous search term from the last request."""
        if not context.requests:
            return "None"
        
        last_request = context.requests[-1]
        return last_request.search_term if last_request.search_term else "None"