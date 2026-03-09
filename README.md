# SMILE Chatbot Template API
<a href="https://github.com/alrey-smile/smile-chatbot-template-api/actions/workflows/deploy.yml">
   <img src="https://github.com/alrey-smile/smile-chatbot-template-api/actions/workflows/deploy.yml/badge.svg?branch=develop" height="20" alt="GitHub Actions Status">
</a>

FastAPI service that exposes a Bot Framework-compatible chat endpoint backed by Retrieval-Augmented Generation (RAG) and Conversational Search pipelines for the SMILE virtual assistant. It orchestrates Azure and GCP services, and LangChain components to deliver grounded responses while emitting telemetry through Azure Monitor.

## Features
- `/api/v1/messages` endpoint ready for Azure Bot Emulator or Bot Service channels.
- `/api/v1/chat` endpoint ready for RAG pipeline combining Azure and GCP services for vector retrieval, history persistence, and language models.
- `/api/v1/setup` endpoint for configuring conversational search attribute_set and filters.
- `/api/v1/search` endpoint for conversational search.
- `/api/v2/search` secured (OAuth2 - Azure AD) endpoint for conversational search.
- `/docs`endpoint for **Swagger UI** (with your Azure AD OAuth2 config)
- Application-level telemetry via Azure Monitor OpenTelemetry exporter.
- Health probes at `/` and `/health` (future feature: production-ready Docker and Compose definitions).

## Project Structure
- `src/app.py`: FastAPI entry point, lifespan hooks, CORS, and global exception handling.
- `src/routers/`: Bot Framework routing and conversation logic wiring.
- `src/domain/`: Clean-Architecture Domain layer defining models, core business entities and rules 
- `src/application/`: Clean-Architecture Application layer defining RAG and Conversational Search orchestration services.
- `src/infrastructure/`: Azure and GCP integrations.
- `docs/`: Supplementary guides for local setup, configuration, and deployment.

## Prerequisites
- Python 3.11+ (3.11 used in the Docker image) with `pip` and `python3-venv`.
- Azure resources (OpenAI, AI Search, Cosmos DB, App Configuration, Key Vault) with credentials exposed through environment variables.
- GCP resources (Vertex, Firestore, GCS)
- Prompts deployed in LangSmith platform (provide a LangSmith key) 
- Optional: Docker 24+ and Docker Compose v2 for containerized runs.

## Quick Start
1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
2. Provide configuration secrets in a `.env` file (see below) or export them as environment variables.
3. Launch the API locally:
   ```bash
   uvicorn src.app:app --host 0.0.0.0 --port 3978 --reload
   ```
4. Connect the RAG endpoint `http://localhost:3978/api/chat` or Conversational Search endpoint `http://localhost:3978/api/search` to exchange messages.
5. In this version, the calls must be sent with a GUID `user_id`, and a `session_id` received after the first call to connect to the history:
   ```bash
   curl --location 'http://localhost:3978/api/chat' \
   --header 'Content-Type: application/json' \
   --data '{
      "user_id": "00000000-0000-0000-0000-000000000000",
      "session_id": "00000000-0000-0000-0000-000000000000", 
      "message": "This is a message"  
   }'
   ```

## Configuration
Refer to `docs/setup.md` for the detailed configuration matrix and `docs/deployment.md` for production guidance.

## Docker (not in this version)
Run the service in a container with the provided assets:
```bash
docker compose up --build
```
Ensure a `.env` file sits beside `docker-compose.yml`; the API exposes port `3978` and includes an HTTP health check.

## Useful Commands
- `pytest`: Add and run tests as you extend the service.
- `uvicorn src.app:app --reload`: Fast reload loop for local development.
- `python -m pip install -r requirements.txt`: Re-install dependencies after updates.

## Additional Resources
- [`docs/setup.md`](docs/setup.md): Environment provisioning, configuration flow, and secrets management.
- [`docs/azure_deployment.md`](docs/azure_deployment.md): Azure setup checklist and operational tips.
- [`infrastructure/terraform/README.md](infrastructure/terraform/README.md): Azure setup via **Terraform**
- [`docs/ollama.md`](docs/ollama.md): Install Ollama (LLM) locally
