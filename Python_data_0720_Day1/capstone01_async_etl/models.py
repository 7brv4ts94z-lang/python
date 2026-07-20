from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    id: int
    name: str
    category: str
    price: float = Field(gt=0)

    @field_validator("category")
    @classmethod
    def lower_category(cls, value: str) -> str:
        return value.strip().lower()
