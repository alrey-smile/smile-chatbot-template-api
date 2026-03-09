from typing import Annotated, List
from fastapi import Depends

from domain.models import SearchContext, UserRequestDto, ProductFilterDetectionResult, FilterValue
from domain.services.database import DatabaseRequestService, DatabaseAttributesSetupService
from domain.logger import ContextLogger

from application.agents import FilterDetectionAgent, FilterValueExtractionAgent

from dependencies import inject_request_db_service, inject_attribute_db_service, inject_logger

class RequestManager:
    """Coordinates retrieval, enrichment, and persistence of conversational search requests."""

    def __init__(
            self, 
            request_db_service: Annotated[DatabaseRequestService, Depends(inject_request_db_service)],
            attribute_set_db_service : Annotated[DatabaseAttributesSetupService, Depends(inject_attribute_db_service)],
            filter_detection_agent: Annotated[FilterDetectionAgent, Depends(FilterDetectionAgent)],
            filter_value_extraction_agent: Annotated[FilterValueExtractionAgent, Depends(FilterValueExtractionAgent)],
            logger: Annotated[ContextLogger, Depends(inject_logger)]):
        """Persist injected dependencies used to process conversational requests."""
        self.request_db_service = request_db_service
        self.attribute_set_db_service = attribute_set_db_service
        self.filter_detection_agent = filter_detection_agent
        self.filter_value_extraction_agent = filter_value_extraction_agent
        self.logger = logger


    def get_requests(self, context:SearchContext) -> SearchContext:
        """Populate the context with stored requests for the current user session."""
        requests:List[UserRequestDto] = self.request_db_service.get_requests(
            user_id=context.user_id, 
            session_id=context.session_id
        ) if not context.is_first_call else []
        context.requests = requests
        self.logger.debug_context(
            message=f"Got {len(requests)} requests." if not context.is_first_call else "No requests yet.",
            context=context
        )
        return context
    
    def upsert_requests(self, context:SearchContext):
        """Persist the latest request payloads tracked on the context."""
        for request in context.requests:
            self.request_db_service.update_request(request)
        self.logger.debug_context(
            message=f"Upsert {len(context.requests)} requests.",
            context=context
        )
    
    def build_requests(self, context:SearchContext) -> SearchContext:
        """
        Derive detected filter values for each attribute set and update request objects.

        Returns the context after attaching `request_chain_results` and updating request data.
        """
        request_chain_results:List[ProductFilterDetectionResult] = []
        term = context.search_term
        
        # Get the filter list of the product
        if term:
            refinement_question, detected_filters = self._extract_filters(context=context)
            detected_result = ProductFilterDetectionResult(
                search_term=term,
                ai_question=refinement_question,
                detected_filters=[]
            )
            request_chain_results.append(detected_result)

        # Find request corresponding to the search_term (or create it)
        corresponding_request = next((req for req in context.requests if req.search_term == term), None)
        if not corresponding_request:
            corresponding_request = self.request_db_service.create_request(
                user_id=context.user_id,
                session_id=context.session_id,
                search_term=term,
                data={}
            )
            context.requests.append(corresponding_request)
          
        # Update the request with detected values
        if term:
            for filter in detected_filters:
                detected_result.detected_filters.append(filter)
                corresponding_request.data[filter.code] = filter.value

            filters_log = ",  ".join([f"{f.code}:{f.value}" for f in detected_result.detected_filters])
            self.logger.debug_context(
                message=f"Filters for search term '{term}': [{filters_log}]",
                context=context
            )
        
        context.request_chain_results = request_chain_results
        return context

        
    def _extract_filters(self, context: SearchContext) -> tuple[ str, List[FilterValue]]:
        """Extract filter values from user's message using two-step process.
        
        Args:
            context: SearchContext containing the user's message
            
        Returns:
            List of FilterValue with extracted filter values
        """
        # Step 1: Get all available filters
        available_filters = self.attribute_set_db_service.get_all_filters()
        
        if not available_filters:
            self.logger.debug_context("No filters available", context)
            return "", []
        
        # Step 2: Detect filters + identify missing ones + generate refinement question
        detected = self.filter_detection_agent.invoke(context, available_filters)
        self.logger.debug_context(
            message=f"Detected filters: {detected.detected_filter_codes}",
            context=context
        )
        
        # Step 3: Filter the list to only detected ones
        detected_filter_objects = [
            f for f in available_filters 
            if f.code in detected.detected_filter_codes
        ]
        
        if not detected_filter_objects:
            self.logger.debug_context("No filters detected in user message", context)
            return "", []
        
        # Step 4: Extract values for detected filters
        filter_values_model = self.filter_value_extraction_agent.invoke(context, detected_filter_objects)
        
        # Step 5: Convert to FilterValue objects
        result: List[FilterValue] = []
        filter_values_dict = filter_values_model.model_dump()
        
        for filter_obj in detected_filter_objects:
            extracted_value = filter_values_dict.get(filter_obj.code)
            
            if extracted_value:
                result.append(FilterValue(
                    label=filter_obj.label,
                    code=filter_obj.code,
                    type=filter_obj.type,
                    description=filter_obj.description,
                    value=extracted_value
                ))
        
        self.logger.debug_context(
            message=f"Extracted {len(result)} filter values",
            context=context
        )

        return detected.refinement_question, result
