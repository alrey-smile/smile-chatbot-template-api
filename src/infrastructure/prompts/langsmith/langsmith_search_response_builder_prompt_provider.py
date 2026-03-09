from typing import Annotated, List
from fastapi import Depends
from abc import ABC, abstractmethod

from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

from domain.models import SearchContext, FilterDto
from application.prompts import RagMainPromptProvider

from config import Settings, get_settings

class FilterStatusStrategy(ABC):
    
    def __init__(self, comparer):
        self.comparer = comparer 

    def apply(self, nb_detected_filters:int, nb_used_filters:int)-> bool:
        return self.comparer(nb_detected_filters, nb_used_filters)

    @abstractmethod
    def get_filter_information(self, context:SearchContext) -> str:
        pass

class FilterStatusNoUsedFilterStrategy(FilterStatusStrategy):
    def __init__(self):
        super().__init__(lambda _, nb_used_filters: nb_used_filters == 0)

    def get_filter_information(self, context:SearchContext) -> str:
        return "None of the detected filter was used in the search."

class FilterStatusOneUsedFilterStrategy(FilterStatusStrategy):
    def __init__(self):
        super().__init__(lambda _, nb_used_filters: nb_used_filters == 1)

    def get_filter_information(self, context:SearchContext) -> str:
        used_filter = context.search_used_filters[0].label
        return f"Only the filter {used_filter} was used in the search."

class FilterStatusMinusOneUsedFilterStrategy(FilterStatusStrategy):
    def __init__(self):
        super().__init__(lambda nb_detected_filters, nb_used_filters: nb_used_filters + 1 == nb_detected_filters)

    def get_filter_information(self, context:SearchContext) -> str:
        used_codes = {f.code for f in context.search_used_filters}
        unused_filters = [f for f in context.get_valued_filters() if f.code not in used_codes]
        unused_filter = unused_filters[0].label
        return f"The filter {unused_filter} was not used in the search."

class FilterStatusAllUsedFilterStrategy(FilterStatusStrategy):
    def __init__(self):
        super().__init__(lambda nb_detected_filters, nb_used_filters: nb_used_filters == nb_detected_filters)

    def get_filter_information(self, context:SearchContext) -> str:
        return "All of the detected filter were used in the search."
    
class InstructionsStrategy(ABC):
    def __init__(self, comparer):
        self.comparer = comparer 

    def apply(self, nb_products:int)-> bool:
        return self.comparer(nb_products)

    @abstractmethod
    def get_instructions(self) -> str:
        pass

class TooManyProductsInstructionsStrategy(InstructionsStrategy):
    def __init__(self):
        super().__init__(lambda nb_products: nb_products > 10)

    def get_instructions(self) -> str:
        instructions = [
            "\t- Acknowledge briefly that there are many options",
            "\t- Flow naturally into 2-3 specific suggestions to narrow results:",
            "\t\t* Add unused filters from {all_filters}",
            "\t\t* Tighten range filters (price, size, etc.)",
            "\t\t* Focus on key criteria for this product type",
            "\t- Weave suggestions together naturally, not as a bullet list"
        ]
        return "\n".join(instructions)
    
class FewProductsInstructionsStrategy(InstructionsStrategy):
    def __init__(self):
        super().__init__(lambda nb_products: nb_products < 3)

    def get_instructions(self) -> str:
        instructions = [
            "\t- Acknowledge the limited selection briefly",
            "\t- Flow into 2-3 specific suggestions to broaden results:",
            "\t\t* Remove or relax restrictive filters",
            "\t\t* Widen range filters",
            "\t\t* Try alternative search terms or categories",
            "\t- Present as natural conversation, not structured points"
        ]
        return "\n".join(instructions)

class OkProductsInstructionsStrategy(InstructionsStrategy):
    def __init__(self):
        super().__init__(lambda nb_products: nb_products >= 3 and nb_products <= 10)

    def get_instructions(self) -> str:
        instructions = [
            "\t- Briefly confirm this is a good selection to review",
            "\t- Mention casually that filters can still be adjusted if needed",
            "\t- Keep very short (1 sentence)"
        ]
        return "\n".join(instructions)
    
class LangsmithSearchResponseBuilderPromptProvider(RagMainPromptProvider):

    def __init__(self, settings: Annotated[Settings, Depends(get_settings)]):
        self.client = Client(api_key=settings.langchain_api_key)
        self.prompt_name = settings.elasticsuite_search_response_builder_prompt_name
        self.filter_information_strategies:List[FilterStatusStrategy] = [
            FilterStatusNoUsedFilterStrategy(),
            FilterStatusOneUsedFilterStrategy(),
            FilterStatusMinusOneUsedFilterStrategy(),
            FilterStatusAllUsedFilterStrategy()
        ]
        self.instructions_strategies:List[InstructionsStrategy] = [
            TooManyProductsInstructionsStrategy(),
            FewProductsInstructionsStrategy(), 
            OkProductsInstructionsStrategy()
        ]

    def get_prompt(self, search_context:SearchContext) -> ChatPromptTemplate:
        
        rag_prompt:ChatPromptTemplate = self.client.pull_prompt(self.prompt_name)

        # {product_name}
        product_name = search_context.search_term

        # {nb_products}
        nb_products = search_context.search_total_count

        # {nb_product_show}
        nb_product_show = search_context.max_products

        # {product_list_show}
        product_list_show = '\n'.join([
            f"\t* {item.name} - {item.price}" 
            for item in search_context.search_result[:nb_product_show]
        ])

        # {all_filters} - combine used and available filters, deduplicate by code
        all_filters_dict: dict[str, FilterDto] = {}
        for f in search_context.search_used_filters:
            all_filters_dict[f.code] = f
        for f in search_context.search_available_filters:
            if f.code not in all_filters_dict:
                all_filters_dict[f.code] = f
        
        all_filters = "\n".join([
            f"\t* {filter.label}"
            for filter in all_filters_dict.values()
        ])

        # {detected_filters}
        detected_filters = "\n".join([
            f"\t* {f.label}: {f.value}"
            for f in search_context.get_valued_filters()
        ])

        # {filters_information}
        nb_detected_filters = len(search_context.get_valued_filters())
        nb_used_filters = len(search_context.search_used_filters)
        filters_information = ""
        for strategy in self.filter_information_strategies:
            if strategy.apply(nb_detected_filters, nb_used_filters):
                filters_information = strategy.get_filter_information(search_context)
                break
        
        # {instructions}
        instructions = ""
        for strategy in self.instructions_strategies:
            if strategy.apply(nb_products):
                instructions = strategy.get_instructions()
                break

        rag_prompt = rag_prompt.partial(
            product_name=product_name,
            nb_products=nb_products, 
            nb_product_show=nb_product_show,
            product_list_show=product_list_show,
            all_filters=all_filters,
            detected_filters=detected_filters,
            filters_information=filters_information,
            instructions=instructions, 
            lang=search_context.search_lang.lang_name
        )

        return rag_prompt