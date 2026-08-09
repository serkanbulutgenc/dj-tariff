from apps.tariffs.documents import TariffNodeDocument
from apps.tariffs.models import TariffNode
from django.shortcuts import get_object_or_404
from elasticsearch.dsl import Q
from ninja import Query
from ninja import Router

from .schemas import SearchResultSchema
from .schemas import TariffNodeBaseSchema
from .schemas import TariffNodeDetailSchema

router = Router(tags=["tariffs"])


@router.get(
    "/tree",
    response=list[TariffNodeBaseSchema],
    summary="Get taiff tree nodes",
    description="Get TariffNode tree nodes",
)
def get_tree_nodes(request, parent_id: int | None = None):
    if parent_id:
        parent = get_object_or_404(TariffNode, id=parent_id)
        return parent.get_children()
    return TariffNode.get_root_nodes()


"""
@router.get("/{code}", response=TariffNodeDetailSchema)
def get_tariff_by_code(request, code: str):
    return get_object_or_404(TariffNode, code=code)
"""


@router.get("/{code}/ancestors", response=list[TariffNodeBaseSchema])
def get_tariff_ancestors(request, code: str):
    node = get_object_or_404(TariffNode, code=code)
    return node.get_ancestors()


@router.get("/search", response=SearchResultSchema)
def search_tariffs(
    request,
    q: str = Query(..., description="Search by code or keyword"),
    node_type: str | None = None,
    page: int = 1,
    size: int = 20,
):
    start = (page - 1) * size
    end = start + size

    search_query = Q(
        "multi_match",
        query=q,
        fields=["code^3", "code^2", "name"],
        fuzziness="AUTO",
    )

    s = TariffNodeDocument.search().query(search_query)

    if node_type:
        s = s.filter("term", node_type=node_type)

    response = s[start:end].execute()

    results = [
        TariffNodeBaseSchema(
            id=hit.id,
            code=hit.code,
            name=hit.name,
            node_type=hit.node_type,
            depth=hit.depth,
            is_leaf=hit.is_leaf,
        )
        for hit in response
    ]

    return SearchResultSchema(
        total=response.hits.total.value,
        page=page,
        size=size,
        results=results,
    )
