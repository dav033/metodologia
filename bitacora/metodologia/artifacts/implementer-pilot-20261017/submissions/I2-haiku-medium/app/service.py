"""Service layer for paginated item listing."""
from app.repository import DEFAULT_LIMIT


def list_items(repo, limit=DEFAULT_LIMIT, cursor=None):
    return repo.page(limit=limit, cursor=cursor)
