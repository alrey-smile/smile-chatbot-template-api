variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "Development"
    Project     = "MAYA"
    ManagedBy   = "Terraform"
  }
}

variable "resource_group_name" {
    description = "Name of the resource group"
    type        = string
    default     = "maya-dev-rg"
}

variable "location" {
    description = "Azure region for resources"
    type        = string
    default     = "francecentral"
}

variable "app_service_name" {
    description = "Name of the App Service"
    type        = string
    default     = "maya-dev-api"
}

variable "python_version" {
    description = "Python version for the runtime"
    type        = string
    default     = "3.11"
}

# New variable for app settings
variable "app_settings" {
    description = "Application settings (environment variables) for the App Service"
    type        = map(string)
    default     = {
        "PROJECT_NAME" = "smile-chatbot-template"
		"LOG_LEVEL" = "DEBUG"
		"SEARCH_LANG" = "FR"
		"AZURE_COSMOS_DATABASE" = "chatbot"
		"AZURE_COSMOS_DOCUMENT_CONTAINER" = "embeddings"
		"AZURE_COSMOS_DOCUMENT_PARTITION_KEY" = "doc_type"
		"AZURE_COSMOS_HISTORY_CONTAINER" = "history"
		"AZURE_COSMOS_HISTORY_PARTITION_KEY" = "user_id"
		"AZURE_COSMOS_ATTRIBUTES_CONTAINER" = "attributes"
		"AZURE_COSMOS_ATTRIBUTES_PARTITION_KEY" = "project_id"
		"AZURE_COSMOS_FILTERS_CONTAINER" = "filters"
		"AZURE_COSMOS_FILTERS_PARTITION_KEY" = "attribute_id"
		"AZURE_COSMOS_REQUEST_CONTAINER" = "requests"
		"AZURE_COSMOS_REQUEST_PARTITION_KEY" = "user_id"
    }
}

variable "key_vault_name" {
    description = "Name of the Key Vault"
    type        = string
    default     = "maya-dev-kv"
}

variable "app_insights_name" {
  description = "Name of the Application Insights"
  type        = string
  default     = "maya-dev-ais"
}

variable "cosmos_db_account_name" {
  description = "Name of the Cosmos DB account"
  type        = string
  default     = "maya-dev-cosmos-db"
}

variable "cosmos_db_database_name" {
  description = "Name of the Cosmos DB database"
  type        = string
  default     = "chatbot"
}

variable "cosmos_db_containers" {
  description = "List of Cosmos DB containers with their partition keys"
  type = list(object({
    name          = string
    partition_key = string
  }))
  default = [
    {
      name          = "embeddings"
      partition_key = "/doc_type"
    },
    {
      name          = "history"
      partition_key = "/user_id"
    },
    {
      name          = "attributes"
      partition_key = "/project_id"
    },
    {
      name          = "filters"
      partition_key = "/attribute_id"
    },
    {
      name          = "requests"
      partition_key = "/user_id"
    }
  ]
}

variable "openai_account_name" {
  description = "Name of the Azure OpenAI account"
  type        = string
  default     = "maya-dev-openai"
}

variable "openai_sku" {
  description = "SKU for Azure OpenAI (S0 = Standard)"
  type        = string
  default     = "S0"
}

variable "openai_deployments" {
  description = "List of Azure OpenAI model deployments"
  type = list(object({
    name          = string
    model_name    = string
    model_version = string
    scale_type    = string
    capacity      = number
  }))
  default = [
    {
      name          = "Ada"
      model_name    = "text-embedding-ada-002"
      model_version = "2"
      scale_type    = "Standard"
      capacity      = 1
    },
    {
      name          = "gpt-4o-mini"
      model_name    = "gpt-4o-mini"
      model_version = "2024-07-18"
      scale_type    = "GlobalStandard"
      capacity      = 1
    }
  ]
}

variable "search_service_name" {
  description = "Name of the Azure AI Search service"
  type        = string
  default     = "maya-dev-search"
}

variable "search_sku" {
  description = "SKU for Azure AI Search"
  type        = string
  default     = "basic"
}

variable "search_replica_count" {
  description = "Number of replicas for Azure AI Search"
  type        = number
  default     = 1
}

variable "search_partition_count" {
  description = "Number of partitions for Azure AI Search"
  type        = number
  default     = 1
}