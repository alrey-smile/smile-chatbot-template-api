from typing import Annotated
from fastapi import Depends

from langchain_core.output_parsers.pydantic import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from domain.models import SearchContext
from domain.ai import LlmProvider
from domain.fields import AttributeSetField

from application.prompts import PromptProvider

from dependencies import inject_deep_llm_provider, inject_attribute_set_extraction_prompt
from config import Settings, get_settings


class AttributeSetExtractionAgent:
    """Coordinate attribute set extraction by wiring prompts, parser, and LLM provider."""

    def __init__(self, 
            settings: Annotated[Settings, Depends(get_settings)], 
            llm_agent: Annotated[LlmProvider, Depends(inject_deep_llm_provider)],
            prompt_provider: Annotated[PromptProvider[SearchContext], Depends(inject_attribute_set_extraction_prompt)]):
        """Store injected dependencies used to build the attribute extraction pipeline."""
        self.settings = settings
        self.llm_agent = llm_agent
        self.prompt_provider = prompt_provider
        self.pydantic_object = AttributeSetField

    def invoke(self, context:SearchContext):
        """Return structured attribute data parsed from the LLM response for a user query."""
        output_parser = PydanticOutputParser(pydantic_object=self.pydantic_object)
        format_instructions = output_parser.get_format_instructions()
        prompt_template:ChatPromptTemplate = self.prompt_provider.get_prompt(context)

        prompt_template.append(message=("human", "{question}"))
        messages = prompt_template.format_messages(question=context.exchange, format_instructions=format_instructions)
        output = self.llm_agent.invoke(messages)

        response = output_parser.parse(output.content)
        return response
