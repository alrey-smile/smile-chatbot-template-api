# Azure Infrastructure - Terraform Deployment

This Terraform configuration deploys the complete Azure infrastructure for the a chatbot application, including all required services with proper configuration.

## 📋 Overview

This deployment creates the following Azure resources:

### Core Services
- **App Service** (`maya-dev-api`) - Python 3.11 web application with managed identity
- **App Service Plan** - Basic B1 tier (Linux)
- **Application Insights** (`maya-dev-ais`) - Monitoring and telemetry
- **Key Vault** (`maya-dev-kv`) - Secure secrets management

### AI & Search Services
- **Azure OpenAI** (`maya-dev-openai`) - With deployments:
  - `Ada` - text-embedding-ada-002 (version 2)
  - `gpt-4o-mini` - GPT-4o-mini model (1M tokens/minute)
- **Azure AI Search** (`maya-dev-search`) - Basic tier for vector search

### Database Services
- **Cosmos DB** (`maya-dev-cosmos-db`) - Serverless NoSQL database
  - Database: `chatbot`
  - Containers: `embeddings`, `history`, `attributes`, `filters`, `requests`

## Install Terraform 
```bash
sudo wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(grep -oP '(?<=UBUNTU_CODENAME=).*' /etc/os-release || lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update
sudo apt install terraform
```

## 🎯 Deployment Steps

### 1. Authenticate with Azure CLI 
```bash
az login
```

#### 1.1 Remove any partial state (if needed)
```bash
rm -rf .terraform
rm -f .terraform.lock.hcl
rm -f terraform.tfstate*
```

### 2. Initialize Terraform
Run the initialization command:
```bash
cd infrastructure/terraform
terraform init
```

### 3. Plan the Deployment
Review what Terraform will create:
```bash
terraform plan
```
This will show you all resources that will be created without actually creating them.

### 4. Apply the Configuration
Deploy the resources:
```bash
terraform apply
```
Type `yes` when prompted to confirm.

### 5: Configure AI Search
Create the search **datasource** first:
```bash
./configure_search_datasource.sh
```
Then create the **indexes** and **indexers**:
```bash
az search index create \
  --service-name maya-dev-search \
  --resource-group maya-dev-rg \
  --name index-1 \
  --index-definition @search_index.json

az search indexer create \
  --service-name maya-dev-search \
  --resource-group maya-dev-rg \
  --name indexer-1 \
  --indexer-definition @search_indexer.json
```

### 6. Verify the Deployment
After successful deployment, verify:
```bash
# Check outputs
terraform output

# Verify in Azure CLI
az webapp show --name maya-dev-api --resource-group maya-dev-rg

# Check managed identity
az webapp identity show --name maya-dev-api --resource-group maya-dev-rg
```

### 7. Enable Basic Auth Publishing (If needed)
If Basic Auth for SCM is not enabled by default, you can set it explicitly via Azure CLI:
```bash
az resource update \
  --resource-group maya-dev-rg \
  --name scm \
  --namespace Microsoft.Web \
  --resource-type basicPublishingCredentialsPolicies \
  --parent sites/maya-dev-api \
  --set properties.allow=true
```

### 8. App Service Logs (If needed)
```bash
az webapp log tail --name maya-dev-api --resource-group maya-dev-rg
```

## 🔄 Updating Infrastructure

```bash
# Modify terraform.tfvars or main.tf
terraform plan
terraform apply
```

## 🗑️ Cleanup

```bash
terraform destroy
```
⚠️ **Warning**: Permanently deletes all resources!

## ✅ Deployment Checklist

- [ ] Azure CLI installed and logged in
- [ ] Terraform installed
- [ ] Customized `terraform.tfvars`
- [ ] Run `terraform init`
- [ ] Run `terraform apply`
- [ ] Run `./configure_search_datasource.sh`
- [ ] Create index and indexer
- [ ] Enable SCM Basic Auth in Portal
- [ ] Deploy application code
- [ ] Verify services are running
