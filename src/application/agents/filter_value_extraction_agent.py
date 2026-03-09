from pydantic import ValidationError
from langchain_core.output_parsers.pydantic import PydanticOutputParser
import builtins
from domain.tools import repair_llm_pydantic_answer
from langchain_core.exceptions import OutputParserException
from langchain_core.prompts import ChatPromptTemplate
from domain.fields import build_pydantic_model, PydanticSchema, PriceRangeField
from typing import List, Annotated
from domain.models import  SearchContext, FilterDto
from langchain_core.runnables import RunnableLambda
from domain.ai import LlmProvider
from config import Settings, get_settings
from domain.logger import ContextLogger
from fastapi import Depends
from application.prompts import PromptProvider
from dependencies import inject_deep_llm_provider, inject_logger, inject_filters_value_extraction_prompt

class FilterValueExtractionAgent:
    """Extract filter values from user input without generating counter-requests."""

    def __init__(self, 
            settings: Annotated[Settings, Depends(get_settings)], 
            llm_provider: Annotated[LlmProvider, Depends(inject_deep_llm_provider)],
            prompt_provider: Annotated[PromptProvider, Depends(inject_filters_value_extraction_prompt)],
            logger: Annotated[ContextLogger, Depends(inject_logger)]):
        self.settings = settings
        self.llm_provider = llm_provider
        self.prompt_provider = prompt_provider
        self.logger = logger
        self.attempt = 1

    def invoke(self, context: SearchContext, filters: List[FilterDto]):
        """Extract filter values from user input.
        
        Args:
            context: SearchContext containing the user's message
            filters: List of available FilterDto with their options
            
        Returns:
            Pydantic model instance with extracted filter values
        """
        # Build schemas from available filters
        schemas = [
            PydanticSchema(
                name=filter.code,
                required=True,
                field_type=PriceRangeField if filter.type == "price" else getattr(builtins, filter.options_type or "str"),
                description=filter.description
            )
            for filter in filters
        ]
        
        model_type = build_pydantic_model(schemas)
        output_parser = PydanticOutputParser(pydantic_object=model_type)
        format_instructions = output_parser.get_format_instructions()
        
        # Get prompt from provider
        prompt = self.prompt_provider.get_prompt(context, filters)
        prompt = prompt.partial(format_instructions=format_instructions)
        
        # Build filter descriptions
        filters_declarations = []
        for filter in filters:
            data_type_str = ""
            if filter.type == "price" and filter.options_type == "str":
                data_type_str = " (data-type = string)"
            filters_declarations.append(f"- **{filter.code}**: {filter.description or filter.label}{data_type_str}")
        
        param_filters = "\n".join(filters_declarations)
        
        filter_options_items = []
        for filter in filters:
            if filter.type == "price" and filter.options and len(filter.options) > 0:
                price_values = [float(p) for p in filter.options if p]
                if price_values:
                    min_price = min(price_values)
                    max_price = max(price_values)
                    filter_options = f'"{min_price}-{max_price}"'
                else:
                    filter_options = '""'
            else:
                formatted_options = ", ".join(f'"{option}"' for option in filter.options)
                filter_options = formatted_options
            filter_options_items.append(f"- **{filter.code}**: {filter_options}")
        
        param_filters_options = "\n".join(filter_options_items)
        param_filter_list = ", ".join(f"`{filter.code}`" for filter in filters)
        
        # Add partial variables
        prompt = prompt.partial(
            filters=param_filters,
            filter_list=param_filter_list,
            filter_possible_values=param_filters_options
        )
        prompt.append(("human", "{question}"))
        
        # Run chain with retry
        self.attempt = 1
        def __run_chain(exchange: str):
            self.logger.debug_context(f"Extracting filter values... attempt {self.attempt}", context)
            self.attempt += 1
            chain = prompt | self.llm_provider.get_llm()
            output = chain.invoke({"question": exchange})
            repaired_json = repair_llm_pydantic_answer(json=output.content, schemas=schemas)
            response = output_parser.parse(repaired_json)
            return response
        
        runnable = RunnableLambda(__run_chain)
        response = runnable.with_retry(
            stop_after_attempt=3,
            retry_if_exception_type=(OutputParserException, ValidationError, ValueError),
        ).invoke(context.exchange)
        
        return response