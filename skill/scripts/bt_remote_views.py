"""Compatibility import for the remote API's read-only HTTP views.

The view routes currently live alongside the authenticated API dispatcher. Keep a
named module available to installed clients and split consumers without duplicating
or changing that routing behavior.
"""
from __future__ import annotations

from bt_remote_api import route_get

__all__ = ["route_get"]
