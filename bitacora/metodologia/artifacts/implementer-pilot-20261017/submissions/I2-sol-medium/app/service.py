"""Application entry point for listing a page of items."""


def list_items(repo, limit=20, cursor=None):
    return repo.page(limit=limit, cursor=cursor)
