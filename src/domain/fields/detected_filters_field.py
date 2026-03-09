from pydantic import BaseModel, Field
from typing import List

class DetectedFiltersField(BaseModel):
    """Output model for detected filter codes."""
    detected_filter_codes: List[str] = Field(
        description="List of filter codes detected in the user's message"
    )
    chain_of_thoughts: str = Field(
        description="Explanation of which filters were detected and why"
    )
    refinement_question: str = Field(
        default="",
        description="A natural language question to help the user refine their search based on missing filters. Empty string if no refinement needed."
    )