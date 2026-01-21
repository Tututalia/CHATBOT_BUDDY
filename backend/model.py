
from pydantic import BaseModel
from typing import Optional


class Product(BaseModel):
    id: int
    name: str
    description: str
    price: float
    quantity: int


class CSVProduct(BaseModel):
    product_id: str
    product_name: str
    category: str
    price: float
    online_available: str
    offline_available: str
    offline_stores: str
    festival: str
    season: str
    image_reference: str
