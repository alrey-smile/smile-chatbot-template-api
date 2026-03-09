from typing import List

from domain.models import FilterValue

class ElasticSuiteGraphqlQueryFactory:

    def build_data(
            self,
            filters:List[FilterValue],
            search_term:str, 
            page_size: int):
        # Build variable param declarations (skip empties)
        param_decls = [] 
        filter_args = []
        for detected_filter in filters:
            if self.__not_empty_value(detected_filter):
                param_decls.append(self.__build_param(detected_filter))
                filter_args.append(self.__build_param_definition(detected_filter))
        params_header = ", ".join(["$term: String!"] + param_decls + ["$pageSize: Int = 1"])

        filter_args_str = ", ".join(filter_args)

        query_tale = """
        {
            total_count
            items {
                id
                sku
                name
                price_range { minimum_price { final_price { value currency } } }
                image { url }
                url_key
            }
            page_info { current_page page_size total_pages }
            aggregations { attribute_code frontend_input label options { label value count } }
        }
        """

        query_products = f"products(search: $term filter: {{ {filter_args_str} }} pageSize: $pageSize)"
        query = f"query ({params_header}) {{ {query_products} {query_tale} }}"

        variables = {}
        for detected_filter in [f for f in filters if f.value]: # Exclude filters with empty or zero value
            self.__fill_variables(variables, detected_filter)

        variables["term"] = search_term
        variables["pageSize"] = page_size

        return {"query": query, "variables": variables}
    
    def __fill_variables(self, variables:dict, detected_filter:FilterValue):
        if detected_filter.type == "price":
            if detected_filter.value["max_price"] > 0:
                variables["min_price"] = detected_filter.value["min_price"]
                variables["max_price"] = detected_filter.value["max_price"]
        elif detected_filter.value: 
            variables[detected_filter.code] = detected_filter.value
    
    def __not_empty_value(self, filter:FilterValue):
        if filter.type == "price":
            return filter.value and (filter.value["min_price"] > 0 or filter.value["max_price"] > 0)
        else:
            return filter.value
    
    def __build_param(self, filter: FilterValue) -> str:
        if filter.type == "price":
            return "$min_price: String!, $max_price: String!"
        return f"${filter.code}: String!"

    def __build_param_definition(self, filter: FilterValue) -> str:
        match filter.type:
            case "price":
                return "price: { from: $min_price, to: $max_price }"
            case "decimal":
                return f"{filter.code}: {{ from: ${filter.code} }}"
            case "select" | "multiselect":
                return f"{filter.code}: {{ eq: ${filter.code} }}"
            case "smile_custom_entity" | "text":
                return f"{filter.code}: {{ match: ${filter.code} }}"
            case _:
                raise ValueError(f"Unsupported filter data-type: {filter.type}")