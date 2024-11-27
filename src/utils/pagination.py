from pydantic import BaseModel
from typing import List, TypeVar, Generic


class PaginationParams(BaseModel):
    page: int = 1
    per_page: int = 10

    def skip(self) -> int:
        return (self.page - 1) * self.per_page


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    per_page: int
    total_pages: int


def paginate(
    pagination_params: PaginationParams, paginated_items: List[T], total: int
) -> PaginatedResponse[T]:
    total_pages = (total + pagination_params.per_page - 1) // pagination_params.per_page

    return PaginatedResponse(
        items=paginated_items,
        total=total,
        page=pagination_params.page,
        per_page=pagination_params.per_page,
        total_pages=total_pages,
    )
