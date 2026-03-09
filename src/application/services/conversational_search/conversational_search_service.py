from typing import Annotated, Generator
from fastapi import Depends
from config import Settings, get_settings

from langchain_core.globals import set_verbose, set_debug

from domain.models import SearchContext, SearchServiceResult
from domain.logger import ContextLogger

from application.services.conversational_search import (
    LanguageManager,
    ConversationManager,
    RequestManager,
    SearchManager,
    SearchService, 
)

from dependencies import inject_logger

class ConversationalSearchService(SearchService):
    """Coordinates the end-to-end conversational product search workflow."""

    def __init__(
            self,
            settings: Annotated[Settings, Depends(get_settings)],
            language_manager:Annotated[LanguageManager, Depends(LanguageManager)],
            conversation_manager:Annotated[ConversationManager, Depends(ConversationManager)],
            request_manager:Annotated[RequestManager, Depends(RequestManager)],
            search_manager:Annotated[SearchManager, Depends(SearchManager)],
            logger: Annotated[ContextLogger, Depends(inject_logger)]):
        """
        Initialize the conversational search service with its required dependencies.

        Args:
            settings: Application settings that control runtime flags such as debug mode.
            language_manager: Service responsible for language detection and configuration.
            conversation_manager: Handles conversation state persistence and summarization.
            request_manager: Builds and upserts user product requests.
            search_manager: Executes the product search workflow.
            logger: Context-aware logger for workflow tracing.
        """
        self.settings = settings
        self.language_manager = language_manager
        self.conversation_manager = conversation_manager
        self.request_manager = request_manager
        self.search_manager = search_manager
        self.logger = logger

        # Set the verbosity level based on the DEBUG environment variable
        set_verbose(settings.debug)
        set_debug(settings.debug)

    def invoke(
        self, 
        input_message: str, 
        user_id: str, 
        session_id: str = None,
        max_products: int = 10
    ) -> Generator[SearchServiceResult, None, None]:
        """
        Run the conversational search workflow for the given user input.

        Args:
            input_message: Raw message supplied by the user.
            user_id: Identifier for the user issuing the request.
            session_id: Existing conversation thread identifier, if any.
            max_products: Maximum number of products to return (default: 10).
        
        Yields:
            SearchServiceResult at different pipeline stages with is_final=False,
            then a final SearchServiceResult with is_final=True.
        """

        context = self._get_search_context(input_message, user_id, session_id, max_products)

        # (1) Detect chat language and get (or create) message thread
        context = self.language_manager.configure_languages(input_message, context)
        context = self.conversation_manager.insert_or_create_thread(context)

        # (2) Detect chit-chat and generate response/acknowledgment
        is_chit_chat, context = self.conversation_manager.manage_chit_chat(context)
        yield SearchServiceResult(
            user_id=context.user_id,
            session_id=context.session_id,
            answer=context.ai_answer,
            products=[],
            is_final=is_chit_chat,  # If chit-chat, this is the final response
        )   
        if is_chit_chat:
            return
        
        # (2) Summarize exchange
        context = self.conversation_manager.summarize_exchange(context)

        # (3) Get requests
        context = self.request_manager.get_requests(context)

        # (4) Extract search term & detect new search
        context = self.search_manager.extract_search_term(context)
        
        if context.needs_reset:
            context = self.conversation_manager.reset_search_session(context)
        
        if not context.search_term:
            yield SearchServiceResult(
                user_id=user_id,
                session_id=context.session_id,
                answer="Sorry, we don't sell this product here.",  # -> TODO: response agent
                products=[],
                is_final=True,
            )
            return

        # (5) Build a request for each product that the user is searching for
        context = self.request_manager.build_requests(context)

        # (6) Generate search summary
        search_summary = self.conversation_manager.generate_search_summary(context)
        yield SearchServiceResult(
            user_id=context.user_id,
            session_id=context.session_id,
            answer=search_summary,
            products=[],
            is_final=False,
        )

        # (6.5) Upsert the requests
        self.request_manager.upsert_requests(context)

        # (7) If no product or filter detected
        if not context.search_term:
            yield SearchServiceResult(
                user_id=user_id,
                session_id=context.session_id,
                answer="Sorry, I couldn't find the product(s) you are searching for.", # -> TODO: response agent
                products=[],
                is_final=True,
            )
            return

        # (8) Search OR ask for filters
        context = self.search_manager.search(context)
        
        # (9) Insert the AI message in the DB
        self.conversation_manager.store_ai_answer(context)

        self.logger.info_context("Search workflow complete.", context)

        yield SearchServiceResult(
            user_id=context.user_id,
            session_id=context.session_id,
            answer=context.ai_answer,
            products=context.search_result,
            is_final=True,
        )

    def legacy_invoke(self, input_message: str, user_id: str, session_id: str = None) -> SearchServiceResult:
        """
        Legacy synchronous method for backward compatibility (v1/v2).
        Consumes the stream and returns only the final result.
        """
        final_result = None
        for result in self.invoke_stream(input_message, user_id, session_id):
            if result.is_final:
                final_result = result
        return final_result

    # Get (or create) search context
    def _get_search_context(
            self, 
            input_message: str, 
            user_id: str, 
            session_id: str = None,
            max_products: int = 10,
    ) -> SearchContext:
        return SearchContext(
            input_message=input_message, 
            user_id=user_id, 
            session_id=session_id,
            is_first_call= not session_id,
            max_products=max_products
        )