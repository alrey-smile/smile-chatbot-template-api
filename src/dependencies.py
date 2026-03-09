import logging
from fastapi import Depends

from domain.logger import ContextLogger
from domain.ai import LlmProvider, EmbeddingsProvider, VectorStoreProvider
from domain.models import SearchContext
from domain.api_client import ConversationalSearchClient
from domain.services.database import (
    DatabaseHistoryService, 
    DatabaseDocumentService, 
    DatabaseAttributesSetupService, 
    DatabaseRequestService
)

# Avoid circular dependency injection
from application.agents.search_response_builder_agent import SearchResponseBuilderAgent
from application.prompts import PromptProvider, StaticPromptProvider, RagMainPromptProvider

from domain.agents.language_detector import LanguageDetector
from application.models import RagChatMessage, SearchChatMessage

from infrastructure.gcp.services import GoogleCloudStorageDocumentService, FirestoreHistoryService
from infrastructure.gcp.ai import VertexLlmProvider, VertexVectorStoreProvider
from infrastructure.azure.services import (
    CosmosDbDocumentService, 
    CosmosDbHistoryService, 
    CosmosDBAttributesSetupService,
    CosmosDbRequestService
)
from infrastructure.azure.ai import AzureOpenAiLlmProvider, AzureSearchVectorStoreProvider
from infrastructure.openai.ai import OpenAIEmbeddingsProvider
from infrastructure.search.elastic_suite import (
    ElasticSuiteSearchClient, 
    ElasticSuiteSearchClientMock, 
    ElasticSuiteSearchResponseBuilder
)
from infrastructure.prompts.langsmith import (
    LangsmithAttributeSetExtractionPromptProvider,
    LangsmithFiltersExtractionPromptProvider,
    LangsmithIntentExtractionPromptProvider,
    LangsmithQuestionSummarizerPromptProvider,
    LangsmithRagMainPromptProvider,
    LangsmithSearchResponseBuilderPromptProvider,
    LangsmithEmptySearchResponseBuilderPromptProvider,
    LangsmithSummarizeExchangePromptProvider,
    LangsmithChitChatPromptProvider,
    LangsmithSearchSummaryPromptProvider,
    LangsmithSearchTermExtractionPromptProvider,
    LangsmithFiltersDetectionPromptProvider,
    LangsmithFiltersValueExtractionPromptProvider
)
from infrastructure.ollama.ai import OllamaLlmProvider
from infrastructure.configuration.elastic_suite import ElasticSuiteAttributeSetClient, ElasticSuiteAttributeSetResponseBuilder
from infrastructure.agents.elastic_suite import ElasticSuiteSearchResponseBuilderAgent
#from infrastructure.gcp.agents import LangDetectLanguageDetector
from infrastructure.azure.agents import AzureOpenAILanguageDetector

from config import Settings, get_settings

settings = get_settings()

logger = logging.getLogger("app")
logger.setLevel(logging.INFO if settings.log_level == "INFO" else logging.DEBUG)

def inject_logger() -> ContextLogger:
    return ContextLogger(logger)

def inject_configuration_client(settings: Settings = Depends(get_settings)) -> ElasticSuiteAttributeSetClient:
    return ElasticSuiteAttributeSetClient(
        settings=settings,
        attribute_set_response_builder=ElasticSuiteAttributeSetResponseBuilder()
    )

def inject_language_detector() -> LanguageDetector:
    return AzureOpenAILanguageDetector(
        settings=settings,
        logger=inject_logger()
    )

def inject_embedding_provider(settings: Settings = Depends(get_settings)) -> EmbeddingsProvider:
    """Injects an LLMaaS for Embeddings"""
    provider = settings.embeddings_llm_provider.lower()
    match provider:
        case "openai":
            return OpenAIEmbeddingsProvider(settings)
        case _:
            raise ValueError(f"Unsupported Embeddings LLM provider: {provider}")

def inject_deep_llm_provider(settings: Settings = Depends(get_settings)) -> LlmProvider:
    """Injects an LLMaaS for completion (reasoning)"""
    provider = settings.deep_llm_provider.lower()
    match provider:
        case "azure":
            return  AzureOpenAiLlmProvider(settings)
        case "gcp":
            return VertexLlmProvider(settings)
        case _:
            raise ValueError(f"Unsupported LLM provider: {provider}")

def inject_light_llm_provider(settings: Settings = Depends(get_settings)) -> LlmProvider:
    """Injects an lightweight LLMaaS for completion (reasoning)"""
    provider = settings.light_llm_provider.lower()
    match provider:
        case "ollama":
            return OllamaLlmProvider(settings)
        case "azure":
            return  AzureOpenAiLlmProvider(settings)
        case "gcp":
            return VertexLlmProvider(settings)
        case _:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        
def inject_vector_store_provider(settings: Settings = Depends(get_settings)) -> VectorStoreProvider:
    """Injects a Vector Search provider"""
    provider = settings.retriever_provider.lower()
    match provider:
        case "azure":
            return AzureSearchVectorStoreProvider(
                settings=settings,
                embeddings_provider=inject_embedding_provider(settings)
            )
        case "gcp":
            return VertexVectorStoreProvider(
                settings=settings,
                embeddings_provider=inject_embedding_provider(settings)
            )
        case _:
            raise ValueError(f"Unsupported vector store service provider: {provider}")

def inject_content_db_service(settings: Settings = Depends(get_settings)) -> DatabaseDocumentService:
    """Injects content database service"""
    provider = settings.content_db_provider.lower()
    match provider:
        case "azure":
            return CosmosDbDocumentService(settings)
        case "gcp":
            return GoogleCloudStorageDocumentService(settings)
            #return FirestoreDocumentService(FirestoreDocumentDb(settings))
        case _:
            raise ValueError(f"Unsupported Content DB service provider: {provider}")

def inject_history_db_service_for_RAG(settings: Settings = Depends(get_settings)) -> DatabaseHistoryService:
    """Injects history database service for RAG"""
    provider = settings.history_db_provider.lower()
    match provider:
        case "azure":
            return CosmosDbHistoryService[RagChatMessage](RagChatMessage, settings)
        case "gcp":
            return FirestoreHistoryService[RagChatMessage](RagChatMessage, settings)
        case _:
            raise ValueError(f"Unsupported History DB service provider: {provider}")

def inject_history_db_service_for_search(settings: Settings = Depends(get_settings)) -> DatabaseHistoryService:
    """Injects history database service for Conversational Search"""
    provider = settings.history_db_provider.lower()
    match provider:
        case "azure":
            return CosmosDbHistoryService[SearchChatMessage](SearchChatMessage, settings)
        case "gcp":
            return FirestoreHistoryService[SearchChatMessage](SearchChatMessage, settings)
        case _:
            raise ValueError(f"Unsupported History DB service provider: {provider}")

def inject_request_db_service(settings: Settings = Depends(get_settings)) -> DatabaseRequestService:
    """Injects request database service"""
    provider = settings.request_db_provider.lower()
    match provider:
        case "azure":
            return CosmosDbRequestService(settings)
        case _:
            raise ValueError(f"Unsupported Request DB service provider: {provider}")
        
def inject_attribute_db_service(settings: Settings = Depends(get_settings)) -> DatabaseAttributesSetupService:
    """Injects database service for attribute-set and filters (Conversational Search)"""
    provider = settings.attribute_set_db_provider.lower()
    match provider:
        case "azure":
            return CosmosDBAttributesSetupService(settings)
        case _:
            raise ValueError(f"Unsupported History DB service provider: {provider}")

def inject_conversational_search_api(settings: Settings = Depends(get_settings)) -> ConversationalSearchClient:
    return ElasticSuiteSearchClient(
        settings, 
        ElasticSuiteSearchResponseBuilder(), 
        inject_logger()
    )
    # return ElasticSuiteSearchClientMock(
    #     settings, 
    #     ElasticSuiteSearchResponseBuilder(), 
    #     inject_logger()
    # )

def inject_search_response_agent(settings: Settings = Depends(get_settings)) -> SearchResponseBuilderAgent:
    return ElasticSuiteSearchResponseBuilderAgent(
        settings=settings, 
        llm_provider=inject_deep_llm_provider(settings),
        empty_search_prompt_provider=inject_empty_search_response_prompt(settings),
        not_empty_search_prompt_provider=inject_search_response_prompt(settings)
    )

# PROMPTS

def inject_attribute_set_extraction_prompt(settings: Settings = Depends(get_settings)) -> PromptProvider[SearchContext]:
    return LangsmithAttributeSetExtractionPromptProvider(settings)

def inject_filters_extraction_prompt(settings: Settings = Depends(get_settings)) -> PromptProvider[SearchContext]:
    return LangsmithFiltersExtractionPromptProvider(settings)

def inject_intent_extraction_prompt(settings: Settings = Depends(get_settings)) -> StaticPromptProvider:
    return LangsmithIntentExtractionPromptProvider(settings)

def inject_question_summarizer_prompt(settings: Settings = Depends(get_settings)) -> PromptProvider[SearchContext]:
    return LangsmithQuestionSummarizerPromptProvider(settings)

def inject_rag_main_prompt(settings: Settings = Depends(get_settings)) -> RagMainPromptProvider:
    return LangsmithRagMainPromptProvider(settings)

def inject_search_response_prompt(settings: Settings = Depends(get_settings)) -> StaticPromptProvider:
    return LangsmithSearchResponseBuilderPromptProvider(settings)

def inject_empty_search_response_prompt(settings: Settings = Depends(get_settings)) -> StaticPromptProvider:
    return LangsmithEmptySearchResponseBuilderPromptProvider(settings)

def inject_exchange_summarizer_prompt(settings: Settings = Depends(get_settings)) -> StaticPromptProvider:
    return LangsmithSummarizeExchangePromptProvider(settings)

def inject_chit_chat_prompt(settings: Settings = Depends(get_settings)) -> StaticPromptProvider:
    return LangsmithChitChatPromptProvider(settings)

def inject_search_summary_prompt(settings: Settings = Depends(get_settings)) -> StaticPromptProvider:
    return LangsmithSearchSummaryPromptProvider(settings)

def inject_search_term_extraction_prompt(settings: Settings = Depends(get_settings)) -> StaticPromptProvider:
    return LangsmithSearchTermExtractionPromptProvider(settings)

def inject_filters_detection_prompt(settings: Settings = Depends(get_settings)) -> PromptProvider[SearchContext]:
    return LangsmithFiltersDetectionPromptProvider(settings)

def inject_filters_value_extraction_prompt(settings: Settings = Depends(get_settings)) -> PromptProvider[SearchContext]:
    return LangsmithFiltersValueExtractionPromptProvider(settings)