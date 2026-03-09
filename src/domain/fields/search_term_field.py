from pydantic import BaseModel, Field

class SearchTermField(BaseModel):
    term: str = Field(description="The main product/search term the user is looking for, in the same language as the user's message.")
    chain_of_thoughts: str = Field(description="An explanation of why you extracted this term from the user's message.")
    is_new_search: bool = Field(default=False, description="True if the user is starting a completely new search (radical topic change), False if refining the current search.")