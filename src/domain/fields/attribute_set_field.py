from pydantic import BaseModel, Field
from domain.models import AttributeSetDto

class AttributeSetField(BaseModel):
    product:str = Field(description="The name of the product that the user searches.")
    term:str = Field(description="A short search term (1 to 3 words, **in French**) that best represents what the user is searching for.")
    is_intent:bool = Field(description="Whether the user's request is about searching for a product or not")
    chain_of_thoughts:str = Field(description="An explanation why you chose the value for `product` and `is_intent`")