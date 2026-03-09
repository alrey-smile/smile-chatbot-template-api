from typing import Annotated, List
from fastapi import Depends
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client
from domain.models import SearchContext, FilterDto
from application.prompts import PromptProvider
from config import Settings, get_settings

class LangsmithFiltersDetectionPromptProvider(PromptProvider[SearchContext]):

    def __init__(self, settings: Annotated[Settings, Depends(get_settings)]):
        self.client = Client(api_key=settings.langchain_api_key)
        self.prompt_name = settings.langsmith_filters_detection_prompt_name

    def get_prompt(self, available_filters: List[FilterDto]) -> ChatPromptTemplate:
        prompt: ChatPromptTemplate = self.client.pull_prompt(self.prompt_name)
        
        # Build filter list with codes and labels
        filter_list = "\n".join(
            f"- **{filter.code}**: {filter.label}"
            for filter in available_filters
        )
        
        prompt = prompt.partial(filter_list=filter_list)
        
        return prompt