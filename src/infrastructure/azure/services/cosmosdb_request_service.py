import uuid
from typing import Annotated, List
from fastapi import Depends

from azure.cosmos import exceptions

from domain.services.database import DatabaseRequestService
from domain.models import UserRequestDto

from infrastructure.azure.services import CosmosDb

from config import Settings, get_settings

class CosmosDbRequestService(DatabaseRequestService):
    def __init__(self, settings: Annotated[Settings, Depends(get_settings)]):
        self.database = CosmosDb(
            container=settings.azure_cosmos_request_container,
            partition_key=settings.azure_cosmos_request_partition_key,
            settings=settings
        )

    def create_request(self, user_id:str, session_id:str, search_term:str, data:dict) -> UserRequestDto:
        new_id = str(uuid.uuid4())
        request = UserRequestDto(
            id=new_id,
            user_id=user_id,
            session_id=session_id,
            search_term=search_term,
            data=data
        )
        doc = request.to_dict()
        try:
            created = self.database.get_container().create_item(doc)
        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"Failed to create request in Cosmos DB: {e.message}") from e

        return request

    def get_requests(self, user_id:str, session_id:str) -> List[UserRequestDto]:
        # Because partition key is user_id, pass partition_key=user_id to avoid cross-partition queries.
        query = """
        SELECT c.id, c.user_id, c.session_id, c.search_term, c.data
        FROM c
        WHERE c.session_id = @session_id
        """
        params = [
            {"name": "@session_id", "value": session_id},
        ]

        try:
            items_iter = self.database.get_container().query_items(
                query=query,
                parameters=params,
                partition_key=user_id,
                enable_cross_partition_query=False
            )
            docs = list(items_iter)
        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"Failed to fetch requests from Cosmos DB: {e.message}") from e

        return [UserRequestDto.from_dict(d) for d in docs]

    def update_request(self, request:UserRequestDto):
         # Update ONLY the `data` field (per your comment). We'll do a read-replace cycle.
        try:
            container = self.database.get_container()
            # Read by id + partition key:
            current = container.read_item(item=request.id, partition_key=request.user_id)
        except exceptions.CosmosResourceNotFoundError:
            raise KeyError(f"Request not found: id={request.id}, user_id={request.user_id}")
        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"Failed to read request from Cosmos DB: {e.message}") from e

        # Mutate only the `data` field
        current["data"] = request.data if request.data is not None else {}

        try:
            container.replace_item(item=current["id"], body=current)
        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"Failed to update request in Cosmos DB: {e.message}") from e