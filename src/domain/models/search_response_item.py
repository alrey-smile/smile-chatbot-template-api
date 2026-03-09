from dataclasses import dataclass

@dataclass
class SearchResponseItem:
    id:int
    sku:str
    name:str
    price:str
    image_url:str
    url_key:str

    def to_dict(self):
        return {
            "id":self.id,
            "sku":self.sku,
            "name":self.name,
            "price":self.price,
            "image_url":self.image_url,
            "url_key":self.url_key
        }