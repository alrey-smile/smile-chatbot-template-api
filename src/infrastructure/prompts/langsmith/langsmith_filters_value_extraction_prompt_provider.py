from typing import Annotated, List
from fastapi import Depends
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client
from domain.models import SearchContext, FilterDto
from application.prompts import PromptProvider
from config import Settings, get_settings

class LangsmithFiltersValueExtractionPromptProvider(PromptProvider[SearchContext]):

    def __init__(self, settings: Annotated[Settings, Depends(get_settings)]):
        self.client = Client(api_key=settings.langchain_api_key)
        self.prompt_name = settings.langsmith_filters_value_extraction_prompt_name

    def get_prompt(self, context: SearchContext, filters: List[FilterDto]) -> ChatPromptTemplate:
        prompt: ChatPromptTemplate = self.client.pull_prompt(self.prompt_name)
        
        # Build filter descriptions
        filters_declarations = []
        for filter in filters:
            data_type_str = ""
            if filter.type == "price" and filter.options_type == "str":
                data_type_str = " (data-type = string)"
            filters_declarations.append(f"- **{filter.code}**: {filter.description or filter.label}{data_type_str}")
        
        param_filters = "\n".join(filters_declarations)
        
        # Build filter options
        filter_options_items = []
        for filter in filters:
            if filter.type == "price" and filter.options and len(filter.options) == 2:
                filter_options = f"between {filter.options[0]} and {filter.options[1]}"
            else:
                filter_options = ", ".join(str(option) for option in filter.options)
            filter_options_items.append(f"- **{filter.code}**: {filter_options}")
        
        param_filters_options = "\n".join(filter_options_items)
        param_filter_list = ", ".join(f"`{filter.code}`" for filter in filters)
        
        prompt = prompt.partial(
            filters=param_filters,
            filter_list=param_filter_list,
            filter_possible_values=param_filters_options
        )
        
        return prompt