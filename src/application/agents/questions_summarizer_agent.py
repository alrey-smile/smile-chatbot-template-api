from typing import Annotated
from fastapi import Depends
from config import Settings

from domain.ai import LlmProvider
from domain.models import SearchContext

from application.prompts import PromptProvider

from dependencies import inject_deep_llm_provider, inject_question_summarizer_prompt
from config import Settings, get_settings


class QuestionsSummarizerAgent:
    """Agent that summarizes detected product questions into a single LLM prompt."""

    def __init__(self, 
            settings: Annotated[Settings, Depends(get_settings)], 
            llm_agent: Annotated[LlmProvider, Depends(inject_deep_llm_provider)],
            prompt_provider: Annotated[PromptProvider[SearchContext], Depends(inject_question_summarizer_prompt)]):
        """
        Initialize the agent with configuration, LLM gateway, and prompt templates.

        Parameters:
            settings: Application configuration injected via FastAPI.
            llm_agent: Provider responsible for invoking the LLM.
            prompt_provider: Factory for question summarization prompts.
        """
        self.settings = settings
        self.prompt_provider = prompt_provider
        self.llm_agent = llm_agent
    
    def invoke(self, context:SearchContext):
        questions=context.request_chain_results
        """
        Summarize detected product questions alongside the latest exchange context.

        Parameters:
            last_exchange: Conversation history to condition the prompt.
            questions: Structured product questions detected in the exchange.

        Returns:
            str: LLM-generated summary consolidating the product questions.
        """

        prompt_template = self.prompt_provider.get_prompt(context)
        
        new_questions = [f"- [Product: {question.search_term}] -> {question.ai_question}" for question in questions]

        new_message = '\n'.join(new_questions)
        prompt_template.append(new_message)

        messages = prompt_template.format_messages(questions=new_message)
        output = self.llm_agent.invoke(messages)
        return output.content
