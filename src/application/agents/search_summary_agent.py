from typing import Annotated
from fastapi import Depends
from config import Settings, get_settings
from domain.ai import LlmProvider
from domain.models import SearchContext
from application.prompts import StaticPromptProvider
from dependencies import inject_deep_llm_provider, inject_search_summary_prompt

class SearchSummaryAgent:
    """Generates a natural summary of the search about to be performed."""

    def __init__(
        self,
        settings: Annotated[Settings, Depends(get_settings)],
        llm_agent: Annotated[LlmProvider, Depends(inject_deep_llm_provider)],
        prompt_provider: Annotated[StaticPromptProvider, Depends(inject_search_summary_prompt)]
    ):
        """
        Initialize the agent with configuration, LLM gateway, and prompt templates.

        Parameters:
            settings: Application configuration injected via FastAPI.
            llm_agent: Provider responsible for invoking the LLM.
            prompt_provider: Factory for search summary prompts.
        """
        self.settings = settings
        self.llm_agent = llm_agent
        self.prompt_provider = prompt_provider

    def invoke(self, context: SearchContext) -> str:
        """
        Generate a summary sentence for the search.
        
        Parameters:
            context: SearchContext containing product, filters, and language info
            
        Returns:
            str: A natural summary sentence confirming the search
        """
        filters_summary = self._build_filters_summary(context)
        
        prompt_template = self.prompt_provider.get_prompt()
        
        # Build the question string that the prompt expects
        question = f"Provide a short summary of a search for {context.search_term} with filters: {filters_summary} that will complete naturaly your last reponse: {context.ai_answer}"
        
        # Use partial() to pre-fill the question variable
        prompt_template = prompt_template.partial(
            question=question,
            output_language=context.chat_lang.lang_name
        )
        
        messages = prompt_template.format_messages()
        output = self.llm_agent.invoke(messages)
        
        return output.content

    def _build_filters_summary(self, context: SearchContext) -> str:
        """Build a readable summary of detected filters."""
        if not context.get_valued_filters():
            return "No specific filters"
        
        filters_text = []
        for filter_value in context.get_valued_filters():
            if filter_value.type == "price":
                min_p = filter_value.value.get("min_price", 0)
                max_p = filter_value.value.get("max_price", 0)
                filters_text.append(f"Price: {min_p}-{max_p}€")
            else:
                filters_text.append(f"{filter_value.code}: {filter_value.value}")
        
        return ", ".join(filters_text)