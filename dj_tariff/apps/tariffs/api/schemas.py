from ninja import Schema


class TariffNodeBaseSchema(Schema):
    id: int
    code: str | None = None
    name: str


class TariffNodeDetailSchema(TariffNodeBaseSchema):
    node_type: str
    depth: int
    is_leaf: bool


class TariffTreeSchema(TariffNodeBaseSchema):
    children: list[TariffTreeSchema] = []


class SearchResultSchema(Schema):
    total: int
    page: int
    size: int
    results: list[TariffNodeBaseSchema]
