from domain.ai import LlmProvider
from domain.models import SearchResponseItem, FilterValue

# Avoid circular dependency injection
from application.agents.search_response_builder_agent import SearchResponseBuilderAgent
from application.prompts import StaticPromptProvider
from config import Settings

class ElasticSuiteSearchResponseBuilderAgent(SearchResponseBuilderAgent):

    def __init__(self, 
            settings: Settings,
            llm_provider: LlmProvider,
            empty_search_prompt_provider: StaticPromptProvider,
            not_empty_search_prompt_provider: StaticPromptProvider):
        super().__init__(settings, llm_provider, empty_search_prompt_provider, not_empty_search_prompt_provider)


    def build_filter_value_expression(self, filter:FilterValue):

        # TODO : if the value in the request is 0 and not in the list of possible values : put "(not entered by the user)" in the prompt
        # filter_dto = next([f.code == filter for f in filters])
        # if not filter_dto:
        #     raise KeyError(f"Error filter value ({filter})")

        if filter.type == "price":
            min_price = filter.value["min_price"]
            max_price = filter.value["max_price"]

            return f"{filter.code}={min_price}-{max_price}" if max_price > 0 else f"{filter.code} -> (not given by the user)"
        else:
            filter_value = filter.value
            return f"{filter.code}={filter_value}" if filter_value in filter.options else f"{filter.code} -> (not given by the user)"
             

    def build_product(self, product:SearchResponseItem):
        return f"{product.name} - {product.price}"