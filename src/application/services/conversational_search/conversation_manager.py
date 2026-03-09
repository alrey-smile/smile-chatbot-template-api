from typing import Annotated, List
from fastapi import Depends

from domain.models import SearchContext
from domain.services.database import DatabaseHistoryService
from domain.fields import ChitChatField
from domain.logger import ContextLogger

from application.agents import ExchangeSummarizerAgent, ChitChatAgent, SearchSummaryAgent
from application.models import SearchChatMessage

from dependencies import inject_history_db_service_for_search, inject_logger

class ConversationManager:
    """Coordinate message persistence and summarization for conversational search sessions."""

    def __init__(
            self,
            summarize_exchange_agent : Annotated[ExchangeSummarizerAgent, Depends(ExchangeSummarizerAgent)],
            chit_chat_agent: Annotated[ChitChatAgent, Depends(ChitChatAgent)],
            search_summary_agent: Annotated[SearchSummaryAgent, Depends(SearchSummaryAgent)],
            history_db_service: Annotated[DatabaseHistoryService, Depends(inject_history_db_service_for_search)],
            logger: Annotated[ContextLogger, Depends(inject_logger)]):
        self.history_db_service = history_db_service
        self.summarize_exchange_agent = summarize_exchange_agent
        self.chit_chat_agent = chit_chat_agent
        self.search_summary_agent = search_summary_agent
        self.logger = logger 

    def manage_chit_chat(self, context:SearchContext) -> tuple[bool, SearchContext]:
        """
        Detect chit-chat and generate appropriate response.
        
        Returns:
            - (True, context) if chit-chat detected → context.ai_answer contains full response
            - (False, context) if actionable → context.ai_answer contains short acknowledgment
        """
        chit_chat:ChitChatField = self.chit_chat_agent.invoke(context)
        context.ai_answer = chit_chat.response
        
        return chit_chat.is_chit_chat, context
        
    def insert_or_create_thread(self, context:SearchContext) -> SearchContext:
        """Persist the user's message, creating a new thread when needed, and update context history."""
        # Insert user message and get the message history
        current_session_id = context.session_id
        if current_session_id:
            new_message = SearchChatMessage.build_human_message(
                session_id=current_session_id,
                user_id=context.user_id, 
                content=context.input_message
            )
            self.history_db_service.upsert_message(new_message)
            context.session_id = current_session_id
            self.logger.debug_context(f"New HUMAN message inserted: {context.input_message}", context)
        else:
            new_message:SearchChatMessage = self.history_db_service.create_message_thread(
                user_id=context.user_id, 
                message=context.input_message
            )
            current_session_id = new_message.session_id
            context.session_id = current_session_id
            self.logger.debug_context(f"New thread created: {context.input_message}", context)
        message_thread:List[SearchChatMessage] = self.history_db_service.get_message_thread(
            user_id=context.user_id, 
            session_id=current_session_id
        )
        context.message_thread = message_thread
        return context
    
    def summarize_exchange(self, context:SearchContext) -> SearchContext:
        """Attach a short exchange summary to the context for downstream agents."""
        # Summarize exchange
        exchange = self.__summarize_exchange(context)
        context.exchange = exchange
        return context
    
    def generate_search_summary(self, context: SearchContext) -> str:
        """Generate a natural summary of the search about to be performed."""
        summary = self.search_summary_agent.invoke(context)
        self.logger.debug_context(f"Search summary generated: {summary}", context)
        return summary
    
    def store_ai_answer(self, context:SearchContext):
        """Store the AI answer in history so future exchanges have full context."""
        self.history_db_service.upsert_message(message=SearchChatMessage.build_ai_message(
            user_id=context.user_id,
            session_id=context.session_id,
            content=context.ai_answer,
            products=context.search_result
        ))
        self.logger.debug_context(f"New AI message inserted: {context.ai_answer}", context)
    
    def reset_search_session(self, context: SearchContext) -> SearchContext:
        """Reset the search session: new thread, clear requests, re-summarize."""
        context.session_id = None
        context.requests = []
        
        context = self.insert_or_create_thread(context)
        context = self.summarize_exchange(context)
        
        self.logger.info_context(f"New search detected. Reset session to {context.session_id}", context)
        return context
            
    # PRIVATE 

    def __summarize_exchange(self, context:SearchContext):
        """Summarize the conversation thread when multiple messages exist, otherwise echo input."""
        exchange = context.input_message
        if len(context.message_thread) > 1:
            exchange = self.summarize_exchange_agent.invoke(context.message_thread)
            self.logger.debug_context(message=f"Exchange summary: {exchange}", context=context)
        else:
            self.logger.debug_context(message=f"Input message: {exchange}", context=context)

        return exchange
