from abc import ABC, abstractmethod

from langchain_core.prompts import ChatPromptTemplate

from domain.ai import LlmProvider
from domain.models import SearchResponseItem, SearchContext, FilterValue

from application.prompts import StaticPromptProvider

from config import Settings

class SearchResponseBuilderAgent(ABC):
    """Base agent responsible for crafting LLM-ready messages from search context data."""

    def __init__(self, 
            settings: Settings,
            llm_provider: LlmProvider,
            empty_search_prompt_provider: StaticPromptProvider,
            not_empty_search_prompt_provider: StaticPromptProvider):
        """Store dependencies needed for preparing prompts and invoking the LLM."""
        self.settings = settings
        self.empty_search_prompt_provider = empty_search_prompt_provider
        self.not_empty_search_prompt_provider = not_empty_search_prompt_provider
        self.llm_provider = llm_provider
    
    def invoke_empty(self, context: SearchContext):
        """Generate a response when search results are empty."""
        request_items = []
        exchange_list = []
        for message in context.message_thread:
            message_type = "Assistant" if message.type == "ai" else "User"
            exchange_list.append(f"- {message_type}: {message.data.content}")

        for request_chain in context.request_chain_results:
            if request_chain.search_term == context.search_term:
                request_items.extend([
                    f"- {self.build_filter_value_expression(filter)}" 
                    for filter in request_chain.detected_filters
                ])

        result_components = [
            "Filters:\n" + '\n'.join(request_items),
            "Exchange:\n" + '\n'.join(exchange_list),
            f"Output Language: {context.chat_lang.lang_name}"
        ]
        
        new_message = '\n'.join(result_components)
        return self.invoke(message=new_message, prompt_template=self.empty_search_prompt_provider.get_prompt())
    
    def invoke_not_empty(self, context: SearchContext):
        return self.invoke(message=context.exchange, prompt_template=self.not_empty_search_prompt_provider.get_prompt(context))

    def invoke(self, message:str, prompt_template:ChatPromptTemplate):
        """Invoke the configured LLM with the provided message and prompt template."""
        
        new_message = ("human", message)

        messages = prompt_template.format_messages(question=new_message)
        output = self.llm_provider.invoke(messages)
        return output.content
    
    @abstractmethod
    def build_filter_value_expression(self, filter:FilterValue):
        """Return a string describing the request/filter pair for LLM consumption."""
        pass
        
    @abstractmethod
    def build_product(self, product:SearchResponseItem):
        """Return a string representation of a product suitable for the LLM prompt."""
        pass
