from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    project_name:str
    environment: str = "local" # Execution environment
    debug: bool = False # Langchain debug level
    log_level: str = "INFO" # General log level
    search_lang:str = "FR" # Preferred language for the conversational search

    azure_ad_client_id: Optional[str] = None # Backend API Client ID (Entra ID)
    azure_ad_tenant_id: Optional[str] = None # Azure Tenant (Directory) ID (Entra ID)
    openapi_client_id: Optional[str] = None  # Frontend Client ID (for Swagger UI to authenticate)
    
    embeddings_llm_provider:str # Name if the embeddings LLMaaS provider
    deep_llm_provider:str # Name of the reasoning LLMaaS provider
    light_llm_provider:str # Name of the lightweight LLMaaS provider
    retriever_provider:str # Name of the Vector Search provider
    content_db_provider:str # name of the content database provider
    history_db_provider:str # Name of the history database provider
    request_db_provider:str # Name of the request structure database provider
    attribute_set_db_provider:str # Name of the database provider for attribute-sets and filters

    openai_api_version: str = "2020-05-10" # OpenAI API version
    openai_api_key: str # OpenAI API key

    azure_cosmos_url: str # Cosmos DB Endpoint
    azure_cosmos_key: str # Cosmos DB key
    azure_cosmos_database: str = "chatbot" # Database name
    azure_cosmos_document_container: str = "embeddings" # Container name for content and embeddings (vectors)
    azure_cosmos_document_partition_key: str = "doc_type" # Document container's partition key  
    azure_cosmos_history_container: str = "history" # Container name for history (chat memory)
    azure_cosmos_history_partition_key: str = "user_id" # Container history's partition key
    azure_cosmos_attributes_container:str = "attributes" # Container name for attributes (search)
    azure_cosmos_attributes_partition_key:str = "project_id" # Container attribute's partition key
    azure_cosmos_filters_container:str = "filters" # Container name for filters (search)
    azure_cosmos_filters_partition_key:str = "attribute_id" # Container filter's partition key
    azure_cosmos_request_container:str = "requests" # Container name for the requests (filters structure and detected values)
    azure_cosmos_request_partition_key:str = "user_id" # Container request's partition key
    
    azure_openai_endpoint: str # Azure OpenAI endpoint
    azure_openai_api_key: str # Azure OpenAI key
    azure_openai_api_version: str # Azure OpenAI API version
    azure_openai_deployment: str # Azure OpenAI deployment name for completion (model)
    azure_openai_embedding_deployment: str # Azure OpenAI deployment name for embeddings (model)
    azure_openai_temperature : float = 0.2 # Azure OpenAI model temperature

    max_history_size: int = 10 # History memory size  
    max_history_token: int = 200 # maximum of history tokens 

    microsoft_app_id: Optional[str] = None
    microsoft_app_password: Optional[str] = None

    applicationinsights_connection_string: Optional[str] = None # App Insights connection string
    pythonunbuffered:int = 1
    
    cors_allowed_origins: Optional[str] = "*" # CORS configuration
    
    azure_search_endpoint: str # Azure AI Search endpoint
    azure_search_key: str # Azure AI Search key
    azure_search_index: str # Azure AI Search default index name
    
    langchain_api_key: str # Langchain API key
    langsmith_contextualize_question_prompt_name: str # Name of the prompt for contextualizing messages
    langsmith_extract_request_definition_prompt_name : str # Name of the prompt for extracting a structured request
    langsmith_rag_system_prompt_name : str # Name of the main system prompt for RAG 
    langsmith_summary_exchange_prompt_name: str # Name of the prompt for message history summarization
    langsmith_intent_extraction_prompt_name: str # Name of the prompt for intent detection
    langsmith_language_detector_prompt_name: str # Name of the prompt for language detection

    # Elastic suite
    langsmith_attribute_set_extraction_prompt_name:str # Name of the prompt for attribute extraction from user request
    langsmith_filters_extraction_prompt_name:str # Name of the prompt for filters extraction from a user request
    langsmith_filters_detection_prompt_name:str # Name of the prompt for filter detection from user request
    langsmith_filters_value_extraction_prompt_name:str # Name of the prompt for filter value extraction
    langsmith_elastic_suite_question_summarizer_prompt_name:str # Name of the prompt for user question summarization
    langsmith_empty_search_response_builder_prompt_name:str # Name of the prompt for empty response (no product found) generation
    langsmith_not_empty_search_response_builder_prompt_name:str # Name of the prompt for NOT empty response (some product found) generation
    langsmith_chit_chat_prompt_name:str # Name of the prompt for detecting Chit-Chat exchanges
    langsmith_search_summary_prompt_name: str # Name of the prompt for search summary
    langsmith_search_term_extraction_prompt_name: str # Name of the prompt for search summary

    elasticsuite_search_response_builder_prompt_name:str

    elastic_suite_api_base_url: str # Base URL for Elastic Suite attributes and filter retrieval 
    elastic_suite_attribute_set_endpoint:str # Elastic Suite endpoint
    elastic_suite_username:str # Elastic Suite API username 
    elastic_suite_password:str # Elastic Suite API password
    # Search
    elastic_suite_search_api_base_url:str # Elastic Suite search API base URL
    elastic_suite_search_api_credentials:str # Elastic Suite search API credentials
    elasticsuite_magento_store_code: str # ElasticSuite magento store code

    rag_k: int = 3 
    rag_score_threshold: float = 0.8
    max_tokens: Optional[int] = 2048
    top_p: Optional[float] = 0.95
    top_k: Optional[int] = 40

    gcp_project_id:str # GCP project ID
    gcp_credentials_path:str # GCP credential file path
    firestore_database_id: str # GCP Firestore database ID
    firestore_document_collection:str = "documents" # GCP Firestore document collection name
    firestore_history_collection:str = "chat_history" # GCP Firestore history collection name 
    gcp_vertex_model_name:str # GCP Vertex model name 
    gcp_vertex_location:str # GCP Vertex location (region)
    gcp_vertex_temperature:str 
    gcp_vertex_vector_location:str # GCP Vertex Vector Search location 
    gcp_vertex_vector_index_id:str # GCP Vertex Vector Search default index ID
    gcp_vertex_vector_endpoint_id:str # GCP Vertex Vector Search endpoint
    gcp_storage_document_bucket_name:str # GCP GCS bucket name
    gcp_storage_document_bucket_collection:str = "documents" # GCP GCS bucket collection name (for content)
        
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

#@lru_cache
def get_settings():
    return Settings()