For simplicity in the notation, we assume that we deploy the application for a costumer called **Maya** (development environment).

## **Step 1: Prerequisites**
Ensure you have the following:
1. **Azure Account** 
2. **Azure CLI** installed - [Download here](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli).
3. **GitHub Repository** - Your FastAPI app should be in a GitHub repo.
4. **Python 3.11** installed locally.

### Create an App Service on Azure
- Name: **maya-dev-api**
- Runtime Stack: Python - 3.11
- App Service Plan: Basic (B1)
- SCM Basic Auth Publishing Credentials: On (*Settings > Configuration > SCM Basic Auth Publishing Credentials*)
- Startup Command (*Settings > Configuration > Stack settings > Startup command*): 
    ```BASH
    PYTHONPATH= uvicorn app:app --host 0.0.0.0 --port $PORT --app-dir src --log-level info
    ```
- Managed Identity: Activated (Settings > Identity > System assigned > Status = On)
- Run the script `data/helper.ipynb` to obtain the environment variables for the App Service. Paste it on (*Settings > Environment variables > App Settings > Advanced edit*). Make sure to enter the name of your key vault service (see below) in the script (KEYVAULT_NAME).

### Create an AppInsights service on Azure
- Name: maya-dev-ais
- Get the connection string (*Overview > Connection string*)

### Create a Cosmos DB service on Azure
- Name: **maya-dev-cosmos-db**
- Type: Cosmos DB for No SQL
- Capacity mode: Serverless
- Databases:
	- Name: `chatbot`
		- Container: `embeddings` - Partition Key: `/doc_type`
    - Container: `history` - Partition key: `/user_id`
    - Container: `attributes` - Partition key: `/project_id`
    - Container: `filters` - Partition key: `attribute_id`
		- Container: `requests` - Partition Key: `/user_id`
- Get the endpoint and access key (*Settings > Keys*)

### Create an OpenAI service on Azure
- Name: **maya-dev-openai**
- Pricing tier: Standard
- Add Deployments (*Overview > Go to Azure Ai Foundry portal -> Shared resources > Deployments*):
	- Embedding Model Name: Ada, Model: text-embedding-ada-002, Version: 2
	- Completion Model Name: gpt-4o-mini, Model: gpt-4o-mini (for staging, set 1M tokens per minute)
- Get key and endpoint (*Resource Management > Keys and Endpoint*)

### Create an AI Search service on Azure
- Name: **maya-dev-search**
- Pricing tier: Basic (if several index)
- Replicas: 1 (No SLA)
- Partitions: 1
- Search units: 1
- Datasource:
    - Data Source: **Azure Cosmos DB**
	- Name: **maya-dev-ds**
	- Cosmos DB account: **maya-dev-cosmos-db** (CosmosDB instance name)
	- Database: **chatbot** (Cosmos DB database)
	- Collection: **embeddings** (Vectors container)
    - Add *Query* if needed. Example:
    ```SQL
    SELECT * 
    FROM c 
    WHERE (c.doc_type = 'PDF') 
        AND c._ts > @HighWaterMark ORDER BY c._ts -- Mandatory
    ``` 
- Add/Configure **Indexes**:
    - Go to *Search Management > Indexes > Add index (JSON)*:
    ```JSON
    {
        "name": "index-1",
        "fields": [
            {
                "name": "id",
                "type": "Edm.String",
                "searchable": false,
                "filterable": false,
                "retrievable": true,
                "stored": true,
                "sortable": false,
                "facetable": false,
                "key": true,
                "synonymMaps": []
            },
            {
                "name": "doc_type",
                "type": "Edm.String",
                "searchable": false,
                "filterable": false,
                "retrievable": true,
                "stored": true,
                "sortable": false,
                "facetable": false,
                "key": false,
                "synonymMaps": []
            },
            {
                "name": "tag",
                "type": "Collection(Edm.String)",
                "searchable": false,
                "filterable": true,
                "retrievable": false,
                "stored": true,
                "sortable": false,
                "facetable": false,
                "key": false,
                "synonymMaps": []
            },
            {
                "name": "content",
                "type": "Edm.String",
                "searchable": true,
                "filterable": false,
                "retrievable": true,
                "stored": true,
                "sortable": false,
                "facetable": false,
                "key": false,
                "synonymMaps": []
            },
            {
                "name": "content_vector",
                "type": "Collection(Edm.Single)",
                "searchable": true,
                "filterable": false,
                "retrievable": true,
                "stored": true,
                "sortable": false,
                "facetable": false,
                "key": false,
                "dimensions": 1536,
                "vectorSearchProfile": "vector-profile-01",
                "synonymMaps": []
            },
            {
                "name": "metadata",
                "type": "Edm.ComplexType",
                "fields": [
                    {
                        "name": "sourceFile",
                        "type": "Edm.String",
                        "searchable": false,
                        "filterable": false,
                        "retrievable": false,
                        "stored": true,
                        "sortable": false,
                        "facetable": false,
                        "key": false,
                        "synonymMaps": []
                    },
                    {
                        "name": "contentType",
                        "type": "Edm.String",
                        "searchable": false,
                        "filterable": false,
                        "retrievable": false,
                        "stored": true,
                        "sortable": false,
                        "facetable": false,
                        "key": false,
                        "synonymMaps": []
                    },
                    {
                        "name": "pageNumber",
                        "type": "Edm.Int64",
                        "searchable": false,
                        "filterable": false,
                        "retrievable": false,
                        "stored": true,
                        "sortable": false,
                        "facetable": false,
                        "key": false,
                        "synonymMaps": []
                    },
                    {
                        "name": "key_words",
                        "type": "Collection(Edm.String)",
                        "searchable": true,
                        "filterable": true,
                        "retrievable": false,
                        "stored": true,
                        "sortable": false,
                        "facetable": false,
                        "key": false,
                        "synonymMaps": []
                    },
                    {
                        "name": "title",
                        "type": "Edm.String",
                        "searchable": true,
                        "filterable": true,
                        "retrievable": false,
                        "stored": true,
                        "sortable": false,
                        "facetable": false,
                        "key": false,
                        "synonymMaps": []
                    }
                ]
            }
        ],
        "scoringProfiles": [],
        "suggesters": [],
        "analyzers": [],
        "normalizers": [],
        "tokenizers": [],
        "tokenFilters": [],
        "charFilters": [],
        "similarity": {
            "@odata.type": "#Microsoft.Azure.Search.BM25Similarity"
        },
        "semantic": {
            "configurations": [
                {
                    "name": "basic_semantic_config",
                    "prioritizedFields": {
                        "titleField": {
                            "fieldName": "metadata/title"
                        },
                        "prioritizedContentFields": [
                            {
                            "fieldName": "content"
                            }
                        ],
                        "prioritizedKeywordsFields": [
                            {
                            "fieldName": "metadata/key_words"
                            }
                        ]
                    }
                }
            ]
        },
        "vectorSearch": {
            "algorithms": [
                {
                        "name": "vector-config-01",
                        "kind": "hnsw",
                        "hnswParameters": {
                        "metric": "cosine",
                        "m": 4,
                        "efConstruction": 400,
                        "efSearch": 500
                    }
                }
            ],
            "profiles": [
                {
                    "name": "vector-profile-01",
                    "algorithm": "vector-config-01"
                }
            ],
            "vectorizers": [],
            "compressions": []
        }
    }
    ```
- Add/Configure **Indexers**:
    - Go to *Search Management > Indexers > Add indexer (JSON)*:
    ```JSON
    {
        "name": "indexer-1",
        "description": "Some description",
        "dataSourceName": "c-search-ds",
        "skillsetName": null,
        "targetIndexName": "index-1",
        "disabled": null,
        "schedule": null,
        "parameters": null,
        "fieldMappings": [],
        "outputFieldMappings": [],
        "cache": null,
        "encryptionKey": null
    }
    ```
- Get the Endpoint and key:
    - *Overview > Url*
    - *Settings > Keys > Primary admin key*

### Create an App Key Vault on Azure
- Name: **maya-dev-kv**
- Role Assignments:
	- Key Vault Administrator: (you)
	- Key Vault Secrets User: App Service (`maya-dev-api`)
- Run the script `data/helper.ipynb` to obtain the secrets for the Key Vault.

### Security

#### App Registration Setup
1. Register the Backend API in Azure Entra ID:
    - Go to *Azure Portal > Azure Entra ID > +Add > App registration*
    - Name: **maya-backend-api**
    - Supported account types: Choose based on your needs (typically "Single tenant")
    - Click *Register*
    - Note down:
        * Application (client) ID
        * Directory (tenant) ID
2. Expose the Backend API
    - In your app registration, go to *Expose an API > Click "Add" next to "Application ID URI"*
    - Accept the default: api://[backend-client-id], or customize it: api://chatbot-backend
    - Click "Save"
3. Add Scope
    - Click *Add a scope*
    - Scope name: `access_as_user`
    - Who can consent:`Admins and users`
    - Admin consent display name: `Access chatbot API`
    - Admin consent description: "Allows the application to access the chatbot API on behalf of the signed-in user"
    - User consent display name: "Access chatbot"
    - User consent description: "Allows the application to access the chatbot on your behalf"
    - State: `Enabled`
    - Click *Add scope*
    - Your scope is now: `api://[backend-client-id]/access_as_user`
4. Configure Backend API Permissions (Optional, if your backend needs to call other Microsoft APIs)
    - In the app registration, go to  *API permissions*
    - If backend doesn't call other APIs: Leave as-is or remove default permissions
    - If backend calls Microsoft Graph:
        * Click *Add a permission > Microsoft Graph > Delegated permissions*
    - Select: `User.Read`, `email`, `profile` (or whatever you need)
    - Click *Add permissions*
    - Click *Grant admin consent for [Tenant]*
5. Register Frontend Application
    - Go to *Azure Portal > Azure Entra ID > +Add > App registration*
    - Name: *chatbot-frontend*
    - Supported account types: "Accounts in this organizational directory only"
    - Redirect URI:
    - Platform: `Single-page application (SPA)`
    - URI: http://localhost:9000 (add production URL later)
    - Click *Register*
    - Note down the Application (client) ID

6. Add Additional Redirect URIs (Frontend)
    - In the frontend App Registration go to  *Authentication > Single-page application > Add URI**
        - `http://localhost:3000` (development)
        - `http://localhost:5173` (if using Vite)
        - `https://oauth.pstmn.io/v1/callback` (for Postman)
        - `https://your-frontend.azurewebsites.net` (production)
    - Go to *Advanced settings > Allow public client flows*: No (leave disabled for SPA)
    - Go to *Supported account types*: Keep as single tenant

7. **Configure Frontend App Permissions:**
    - In frontend app registration: *API permissions > Add a permission > My APIs*
    - Select your backend API (`chatbot-backend-api`)
    - Select the `access_as_user` scope
    - Click *Add permissions*
    - Click *Grant admin consent* (if you have admin rights)

8. **Get Credentials:**
- **Backend API:**
	- Application (client) ID
	- Directory (tenant) ID
- **Frontend:**
	- Application (client) ID
	- Create a client secret: *Certificates & secrets → New client secret*
	- Copy the value immediately

#### Postman configuration for backend testing

1. **Update the local API request**
- Go to *Authorization*
	- **Auth Type**: `OAuth 2.0`
- Go to *Current Token* configuration
	- **Token**: `Azure AD Token`
	- **Header Prefix**: Bearer
- Go to *Configure New Token*
	- **Token Name**: `Azure AD Token`
	- **Grant type**: `Authorization Code`
	- **Callback URL**: `https://oauth.pstmn.io/v1/callback`
	- **Auth URL**: `https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize`
	- **Access Token URL**: `https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token`
	- **Client ID**: `chatbot-frontend` Client ID (use Postman variables)
	- **Client Secret**: `chatbot-frontend` Client Secret (use Postman variables)
	- **Scope**: `api://{BACKEND_CLIENT_ID}/access_as_user`
	- **State**: (empty)
	- **Client Authentication**: `Send as Basic Auth header`

2. **Send the request**
To send the request, you first *Get New Access Token* (Authorization tab) -> *Use token* (this will add the token to the request) and then send the request

---

## **Step 2: Configure Deployment from GitHub using GitHub Actions**

1. **Get the Azure Publish Profile:**
    ```bash
    az webapp deployment list-publishing-profiles --name maya-dev-api --resource-group maya-dev-rg --xml
    ```
    or... go to the Azure Portal (Overview > Download publish profile)
    - Copy the **publish profile** content between
    ```html
    <publishData>...</publishData>
    ```

2. **Add GitHub Secrets:**
   - In **GitHub Repo → Settings → Secrets and variables → Actions → New Repository Secret**
   - Add a secret named **AZURE_WEBAPP_PUBLISH_DEVELOP_PROFILE**
   - Paste the **publish profile** content.

3. **Create GitHub Actions Workflow:**
   In your GitHub repo, create `.github/workflows/deploy.yml` and add the following:

    ```yaml
    name: Deploy FastAPI to Azure

    on:
        push:
            branches:
                - main  # Change to your deployment branch

    jobs:
        build-and-deploy:
            runs-on: ubuntu-latest
            steps:
            - name: Checkout Code
                uses: actions/checkout@v3

            - name: Setup Python
                uses: actions/setup-python@v4
                with:
                    python-version: '3.11'

            - name: Install Dependencies
                run: |
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt

            - name: Deploy to Azure
                uses: azure/webapps-deploy@v2
                with:
                    app-name: "maya-dev-api"
                    publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_DEVELOP_PROFILE }}
                    package: "."
    ```

4. **Commit & Push Changes to GitHub**
    ```bash
    git add .
    git commit -m "Added GitHub Actions deployment"
    git push
    ```

5. **GitHub Actions will deploy your FastAPI app** automatically.

