from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import RunnableLambda
from typing import List, Annotated
from domain.models import SearchContext, FilterDto
from domain.fields import DetectedFiltersField
from domain.ai import LlmProvider
from config import Settings, get_settings
from domain.logger import ContextLogger
from fastapi import Depends
from dependencies import inject_deep_llm_provider, inject_filters_detection_prompt, inject_logger
from application.prompts import PromptProvider
from pydantic import ValidationError

class FilterDetectionAgent:
    """Detect which filters are mentioned in the user's message."""

    def __init__(self, 
            settings: Annotated[Settings, Depends(get_settings)], 
            llm_provider: Annotated[LlmProvider, Depends(inject_deep_llm_provider)],
            prompt_provider: Annotated[PromptProvider, Depends(inject_filters_detection_prompt)],
            logger: Annotated[ContextLogger, Depends(inject_logger)]):
        self.settings = settings
        self.llm_provider = llm_provider
        self.prompt_provider = prompt_provider
        self.logger = logger
        self.attempt = 1

    def invoke(self, context: SearchContext, available_filters: List[FilterDto]) -> DetectedFiltersField:
        """Detect which filters are mentioned in the user's message.
        
        Args:
            context: SearchContext containing the user's message
            available_filters: List of all available FilterDto
            
        Returns:
            DetectedFiltersField with detected filter codes and reasoning
        """
        output_parser = PydanticOutputParser(pydantic_object=DetectedFiltersField)
        format_instructions = output_parser.get_format_instructions()
        
        # Get prompt from provider
        prompt = self.prompt_provider.get_prompt(available_filters)
        prompt = prompt.partial(format_instructions=format_instructions)
        prompt.append(("human", "{question}"))
        
        # Run chain with retry
        self.attempt = 1
        def __run_chain(exchange: str):
            self.logger.debug_context(f"Detecting filters... attempt {self.attempt}", context)
            self.attempt += 1
            chain = prompt | self.llm_provider.get_llm() | output_parser
            response = chain.invoke({"question": exchange})
            return response
        
        runnable = RunnableLambda(__run_chain)
        response = runnable.with_retry(
            stop_after_attempt=3,
            retry_if_exception_type=(OutputParserException, ValidationError, ValueError),
        ).invoke(context.exchange)
        
        self.logger.debug_context(
            message=f"Detected filters: {response.detected_filter_codes}. Reasoning: {response.chain_of_thoughts}",
            context=context
        )
        
        return response