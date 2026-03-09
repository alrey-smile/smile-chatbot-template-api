import uuid
from typing import Annotated, List
from fastapi import Depends

from azure.cosmos import exceptions as cosmos_exceptions

from domain.models import AttributeSetDto, AttributeFilterDto, FilterDto
from domain.services.database import DatabaseAttributesSetupService

from infrastructure.azure.services import CosmosDb

from config import Settings, get_settings

class CosmosDBAttributesSetupService(DatabaseAttributesSetupService):
    def __init__(self, settings: Annotated[Settings, Depends(get_settings)]):
        self.attributes_database = CosmosDb(
            container=settings.azure_cosmos_attributes_container,
            partition_key=settings.azure_cosmos_attributes_partition_key,
            settings=settings
        )
        self.filters_database = CosmosDb(
            container=settings.azure_cosmos_filters_container,
            partition_key=settings.azure_cosmos_filters_partition_key,
            settings=settings
        )
        self.attributes_partition_key = settings.azure_cosmos_attributes_partition_key
        self.attributes_partition_value = settings.project_name
        self.filters_partition_key = settings.azure_cosmos_filters_partition_key

    def insert_attribute_set(self, attribute_set: AttributeSetDto):
        """
        Insert (or upsert) the Attribute Set in the attributes container
        and insert (or upsert) its filters in the filters container.
        """
        attributes_container = self.attributes_database.get_container()
        filters_container = self.filters_database.get_container()

        # Upsert the attribute-set document
        attribute_item = attribute_set.to_dict(self.attributes_partition_key, self.attributes_partition_value)
        attributes_container.upsert_item(attribute_item)

        # Upsert the filters (if any)
        if attribute_set.filters:
            filter_items = [filter.to_dict(attribute_set.attribute_set_id) for filter in attribute_set.filters]
            for it in filter_items:
                filters_container.upsert_item(it)

    def get_attribute_set(self, attribute_set_id: int) -> AttributeSetDto:
        """
        Get the Attribute Set and all its filters.
        """
        attributes_container = self.attributes_database.get_container()

        query = f"SELECT * FROM c WHERE c.{self.attributes_partition_key} = @pk"
        params = [{"name": "@pk", "value": self.attributes_partition_value}]
        attr_items = list(attributes_container.query_items(query=query, parameters=params, enable_cross_partition_query=False))

        if not attr_items:
            # Try fallback: read by id if pk_name == 'id'
            # (In case someone configured the partition key as '/id')
            try:
                item = attributes_container.read_item(item=str(attribute_set_id), partition_key=self.attributes_partition_value)
                attr_items = [item]
            except cosmos_exceptions.CosmosResourceNotFoundError:
                pass

        if not attr_items:
            raise ValueError(f"Attribute set {attribute_set_id} not found")

        attr_item = attr_items[0]

        # Fetch filters
        filters = self.get_filters(attribute_set_id)
        return self.build_dto(attr_item, filters)
    
    def get_attribute_set_by_name(self, attribute_set_name: str) -> AttributeSetDto:
        """
        Find an AttributeSet by its name (exact match) and return it with filters filled.
        Cross-partition query since 'name' is not the partition key.
        """
        attributes_container = self.attributes_database.get_container()

        # Exact match on name
        query = "SELECT TOP 1 c.id, c.attribute_set_id, c.name, c.description FROM c WHERE c.name = @name"
        params = [{"name": "@name", "value": attribute_set_name}]
        items = list(
            attributes_container.query_items(
                query=query,
                parameters=params,
                enable_cross_partition_query=True,
            )
        )

        # Optional: fallback to case-insensitive match if exact not found
        if not items:
            ci_query = "SELECT TOP 1 c.id, c.name, c.description FROM c WHERE LOWER(c.name) = LOWER(@name)"
            items = list(
                attributes_container.query_items(
                    query=ci_query,
                    parameters=params,
                    enable_cross_partition_query=True,
                )
            )

        if not items:
            raise ValueError(f"Attribute set with name '{attribute_set_name}' not found")

        it = items[0]
        attribute_set_id = it.get("attribute_set_id")
        # Fetch and attach filters
        filters: List[AttributeFilterDto] = self.get_filters(attribute_set_id)

        return self.build_dto(items[0], filters)
        

    def load_attribute_sets(self) -> List[AttributeSetDto]:
        """
        Return all AttributeSetDto without fetching filters.
        Uses a single cross-partition query.
        """
        attributes_container = self.attributes_database.get_container()

        # Only select what we need
        query = "SELECT c.id, c.attribute_set_id, c.name, c.code, c.description FROM c"
        items = list(
            attributes_container.query_items(
                query=query,
                parameters=None,
                enable_cross_partition_query=True,
            )
        )

        results: List[AttributeSetDto] = []
        for it in items:
            attribute_set = self.build_dto(it, [])
            filters = self.get_filters(attribute_set_id=attribute_set.attribute_set_id)
            attribute_set.filters = filters
            results.append(attribute_set)
            
        return results

    def insert_filters(self, attribute_set_id: int, filters: List[AttributeFilterDto]):
        """
        Insert (or upsert) filters into the filters container for the given attribute_set_id.
        """
        if not filters:
            return

        filters_container = self.filters_database.get_container()
        items = [filter.to_dict(attribute_set_id) for filter in filters]
        for it in items:
            filters_container.upsert_item(it)

    def get_filters(self, attribute_set_id: int) -> List[AttributeFilterDto]:
        """
        Get all filters belonging to an Attribute Set.
        """
        filters_container = self.filters_database.get_container()

        # Query by partition key (fast path)
        query = f"SELECT * FROM c WHERE c.{self.filters_partition_key} = @pk"
        params = [{"name": "@pk", "value": attribute_set_id}]
        items = list(filters_container.query_items(query=query, parameters=params, enable_cross_partition_query=False))

        # Reconstruct DTOs
        return [AttributeFilterDto.from_dto(it) for it in items]
    
    def get_all_filters(self) -> List[FilterDto]:
        """
        Get all filters from the filters container, grouped by code with deduplicated options.

        Todo pigau: update db structure to avoid the foreach
        """
        filters_container = self.filters_database.get_container()

        query = "SELECT * FROM c"
        items = list(filters_container.query_items(query=query, parameters=None, enable_cross_partition_query=True))

        # Group by code and merge options
        grouped: dict[str, dict] = {}
        for item in items:
            code = item.get("code")
            if code not in grouped:
                grouped[code] = {
                    "attribute_id": item.get("attribute_id"),
                    "label": item.get("label"),
                    "code": code,
                    "type": item.get("type"),
                    "description": item.get("description"),
                    "options": []
                }
            
            # Deduplicate and merge options
            existing_options = grouped[code]["options"]
            new_options = item.get("options", [])
            
            for opt in new_options:
                if opt not in existing_options:
                    existing_options.append(opt)
        
        # Reconstruct DTOs from grouped data
        return [FilterDto.from_dto(grouped_item) for grouped_item in grouped.values()]
    
    def build_dto(self, item:dict, filters:List[AttributeFilterDto]):
        return AttributeSetDto(
                id=item.get("id"),
                attribute_set_id=item.get("attribute_set_id"),
                name=item.get("name", "-unknown-"),
                code=item.get("code", "-unknown-"),
                description=item.get("description", "-"),
                filters=filters,  
            ) 