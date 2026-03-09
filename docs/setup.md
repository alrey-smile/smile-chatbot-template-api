# Installation

Install Python environments:

```bash
sudo apt install python3
sudo apt install python3-pip
sudo apt install python3-ipykernel
sudo apt install python3-venv
sudo apt install python3-dotenv
```

Install required packages using `requirements.txt` file.

**Ctrl+Shift-P** > *Python: Create Environment*

- Select Python installation (3.11.x)
- Select the requirements file
- Delete and recreate existing environment

# Configuration

At start-up, the project loads a set of configurations from different sources (environment variables, configuration files, etc.).

The different sources are loaded following a predefined order. If a configuration is present in more than one source, the last is taken into account:

## Sources order

1. File .env (only dev local)
2. Environment variables
3. Azure app configuration (empty label)
4. Azure app configuration (label == environment)

## Used configurations

| Key | Type | Secret | Description | Default values |
|-|-|-|-|-|
|PROJECT_NAME|string| | | |
|ENVIRONMENT|string| |Execution environment|`local`|
|DEBUG|boolean| |Langchain debug level|`False`|
|LOG_LEVEL|string| |General log level|`INFO`|
|SEARCH_LANG|string| |Preferred language for the conversational search|`FR`|
|EMBEDDINGS_LLM_PROVIDER|string| |Name if the embeddings LLMaaS provider| |
|DEEP_LLM_PROVIDER|string| |Name of the reasoning LLMaaS provider| |
|LIGHT_LLM_PROVIDER|string| |Name of the lightweight LLMaaS provider| |
|RETRIEVER_PROVIDER|string| |Name of the Vector Search provider| |
|CONTENT_DB_PROVIDER|string| |name of the content database provider| |
|HISTORY_DB_PROVIDER|string| |Name of the history database provider| |
|REQUEST_DB_PROVIDER|string| |Name of the request structure database provider| |
|ATTRIBUTE_SET_DB_PROVIDER|string| |Name of the database provider for attribute-sets and filters| |
|OPENAI_API_VERSION|string| |OpenAI API version|`2020-05-10`|
|OPENAI_API_KEY|string|X|OpenAI API key| |
|AZURE_COSMOS_URL|string| |Cosmos DB Endpoint| |
|AZURE_COSMOS_KEY|string|X|Cosmos DB key| |
|AZURE_COSMOS_DATABASE|string| |Database name|`chatbot`|
|AZURE_COSMOS_DOCUMENT_CONTAINER|string| |Container name for content and embeddings (vectors)|`embeddings`|
|AZURE_COSMOS_DOCUMENT_PARTITION_KEY|string| |Document container's partition key|`doc_type`|
|AZURE_COSMOS_HISTORY_CONTAINER|string| |Container name for history (chat memory)|`history`|
|AZURE_COSMOS_HISTORY_PARTITION_KEY|string| |Container history's partition key|`user_id`|
|AZURE_COSMOS_ATTRIBUTES_CONTAINER|string| |Container name for attributes (search)|`attributes`|
|AZURE_COSMOS_ATTRIBUTES_PARTITION_KEY|string| |Container attribute's partition key|`project_id`|
|AZURE_COSMOS_FILTERS_CONTAINER|string| |Container name for filters (search)|`filters`|
|AZURE_COSMOS_FILTERS_PARTITION_KEY|string| |Container filter's partition key|`attribute_id`|
|AZURE_COSMOS_REQUEST_CONTAINER|string| |Container name for the requests (filters structure and detected values)|`requests`|
|AZURE_COSMOS_REQUEST_PARTITION_KEY|string| |Container request's partition key|`user_id`|
|AZURE_OPENAI_ENDPOINT|string| |Azure OpenAI endpoint| |
|AZURE_OPENAI_API_KEY|string|X|Azure OpenAI key| |
|AZURE_OPENAI_API_VERSION|string| |Azure OpenAI API version| |
|AZURE_OPENAI_DEPLOYMENT|string| |Azure OpenAI deployment name for completion (model)| |
|AZURE_OPENAI_EMBEDDING_DEPLOYMENT|string| |Azure OpenAI deployment name for embeddings (model)| |
|AZURE_OPENAI_TEMPERATURE|float| |Azure OpenAI model temperature|`0.2`|
|MAX_HISTORY_SIZE|integer| |History memory size|`10`|
|MAX_HISTORY_TOKEN|integer| |maximum of history tokens|`200`|
|MICROSOFT_APP_ID|string| | |`None`|
|MICROSOFT_APP_PASSWORD|string|X| |`None`|
|AZURE_AD_CLIENT_ID|string| | |`None`|
|AZURE_AD_TENANT_ID|string| | |`None`|
|APPLICATIONINSIGHTS_CONNECTION_STRING|string|X|App Insights connection string|`None`|
|PYTHONUNBUFFERED|integer| | |`1`|
|CORS_ALLOWED_ORIGINS|string| |CORS configuration|`*`|
|AZURE_SEARCH_ENDPOINT|string| |Azure AI Search endpoint| |
|AZURE_SEARCH_KEY|string|X|Azure AI Search key| |
|AZURE_SEARCH_INDEX|string| |Azure AI Search default index name| |
|LANGCHAIN_API_KEY|string|X|Langchain API key| |
|LANGSMITH_CONTEXTUALIZE_QUESTION_PROMPT_NAME|string| |Name of the prompt for contextualizing messages| |
|LANGSMITH_EXTRACT_REQUEST_DEFINITION_PROMPT_NAME|string| |Name of the prompt for extracting a structured request| |
|LANGSMITH_RAG_SYSTEM_PROMPT_NAME|string| |Name of the main system prompt for RAG| |
|LANGSMITH_SUMMARY_EXCHANGE_PROMPT_NAME|string| |Name of the prompt for message history summarization| |
|LANGSMITH_INTENT_EXTRACTION_PROMPT_NAME|string| |Name of the prompt for intent detection| |
|LANGSMITH_LANGUAGE_DETECTOR_PROMPT_NAME|string| |Name of the prompt for language detection| |
|LANGSMITH_ATTRIBUTE_SET_EXTRACTION_PROMPT_NAME|string| |Name of the prompt for attribute extraction from user request| |
|LANGSMITH_FILTERS_EXTRACTION_PROMPT_NAME|string| |Name of the prompt for filters extraction from a user request| |
|LANGSMITH_ELASTIC_SUITE_QUESTION_SUMMARIZER_PROMPT_NAME|string| |Name of the prompt for user question summarization| |
|LANGSMITH_EMPTY_SEARCH_RESPONSE_BUILDER_PROMPT_NAME|string| |Name of the prompt for empty response (no product found) generation| |
|LANGSMITH_NOT_EMPTY_SEARCH_RESPONSE_BUILDER_PROMPT_NAME|string| |Name of the prompt for NOT empty response (some product found) generation| |
|ELASTIC_SUITE_API_BASE_URL|string| |Base URL for Elastic Suite attributes and filter retrieval| |
|ELASTIC_SUITE_ATTRIBUTE_SET_ENDPOINT|string| |Elastic Suite endpoint| |
|ELASTIC_SUITE_USERNAME|string| |Elastic Suite API username| |
|ELASTIC_SUITE_PASSWORD|string|X|Elastic Suite API password| |
|ELASTIC_SUITE_SEARCH_API_BASE_URL|string| |Elastic Suite search API base URL| |
|ELASTIC_SUITE_SEARCH_API_CREDENTIALS|string|X|Elastic Suite search API credentials| |
|RAG_K|integer| | |`3`|
|RAG_SCORE_THRESHOLD|float| | |`0.8`|
|MAX_TOKENS|integer| | |`2048`|
|TOP_P|float| | |`0.95`|
|TOP_K|integer| | |`40`|
|GCP_PROJECT_ID|string| |GCP project ID| |
|GCP_CREDENTIALS_PATH|string| |GCP credential file path| |
|FIRESTORE_DATABASE_ID|string| |GCP Firestore database ID| |
|FIRESTORE_DOCUMENT_COLLECTION|string| |GCP Firestore document collection name|`documents`|
|FIRESTORE_HISTORY_COLLECTION|string| |GCP Firestore history collection name|`chat_history`|
|GCP_VERTEX_MODEL_NAME|string| |GCP Vertex model name| |
|GCP_VERTEX_LOCATION|string| |GCP Vertex location (region)| |
|GCP_VERTEX_TEMPERATURE|string| | | |
|GCP_VERTEX_VECTOR_LOCATION|string| |GCP Vertex Vector Search location| |
|GCP_VERTEX_VECTOR_INDEX_ID|string| |GCP Vertex Vector Search default index ID| |
|GCP_VERTEX_VECTOR_ENDPOINT_ID|string| |GCP Vertex Vector Search endpoint| |
|GCP_STORAGE_DOCUMENT_BUCKET_NAME|string| |GCP GCS bucket name| |
|GCP_STORAGE_DOCUMENT_BUCKET_COLLECTION|string| |GCP GCS bucket collection name (for content)|`documents`|

# Launch

The file `launch.json` allows to run the application only by pressing `F5`.