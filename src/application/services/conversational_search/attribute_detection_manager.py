from typing import Annotated, List
from fastapi import Depends

from domain.fields import AttributeSetField
from domain.models import SearchContext, AttributeSetDto
from domain.services.database import DatabaseAttributesSetupService
from domain.logger import ContextLogger

from application.agents import AttributeSetExtractionAgent

from dependencies import inject_attribute_db_service, inject_logger

class AttributeDetectionManager:
    """Coordinates the retrieval of attribute set metadata and detection of user intent."""

    def __init__(
            self,
            attribute_set_db_service : Annotated[DatabaseAttributesSetupService, Depends(inject_attribute_db_service)],
            attribute_set_extraction_agent: Annotated[AttributeSetExtractionAgent, Depends(AttributeSetExtractionAgent)],
            logger: Annotated[ContextLogger, Depends(inject_logger)]):
        """Store collaborators required for attribute detection."""
        self.attribute_set_db_service = attribute_set_db_service
        self.attribute_set_extraction_agent = attribute_set_extraction_agent
        self.logger = logger

    def detect(self, context:SearchContext) -> SearchContext:
        """Populate the search context with attribute sets and detection results."""
        # Get attribute set list
        attribute_sets:List[AttributeSetDto] = self.attribute_set_db_service.load_attribute_sets()
        context.attribute_sets = attribute_sets

        # Detect product (attribute set)
        detected_attribute_set:AttributeSetField = self.attribute_set_extraction_agent.invoke(context)
        
        self.logger.debug_context(
            message=f"[{detected_attribute_set.is_intent}]: {detected_attribute_set.chain_of_thoughts}",
            context=context
        )
        if detected_attribute_set.is_intent:
            self.logger.debug_context(
                message=f"Attribute set: {detected_attribute_set.product}",
                context=context
            )
        
        context.detected_attribute_set = detected_attribute_set

        return context
