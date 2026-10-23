"""`bitacora_platform.<name>` is the platform namespace of the flat `bt_<name>` modules (REQ-007 T5, D-014).

It adds names, not code: `bitacora_platform.core is bt_core`, the same module object, so there is still one
global ROOT and one copy of every monkeypatched value. No file moved and no flat module was rewritten. The final
package name (the ADR says `bitacora`, which the legacy CLI module occupies) is the owner's decision.

Private engine helpers without a flat counterpart can live directly in this package; setuptools includes them with
the namespace, so adding a helper does not require registering another top-level module in the distribution manifest.
"""
from __future__ import annotations

import importlib
import importlib.abc
import importlib.util
import sys

_PREFIX = __name__ + "."


class _AliasFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self) -> None:
        self._original_specs: dict[str, object] = {}

    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith(_PREFIX):
            return None
        short = fullname[len(_PREFIX):]
        if not short or "." in short or importlib.util.find_spec("bt_" + short) is None:
            return None
        return importlib.util.spec_from_loader(fullname, self)

    def create_module(self, spec):
        module = importlib.import_module("bt_" + spec.name[len(_PREFIX):])
        self._original_specs[spec.name] = module.__spec__
        return module

    def exec_module(self, module) -> None:
        # The import machinery stamped the alias spec on the shared module object; give it back its own.
        for name, original in list(self._original_specs.items()):
            if sys.modules.get(name) is module or getattr(module, "__name__", "") == "bt_" + name[len(_PREFIX):]:
                module.__spec__ = original
                self._original_specs.pop(name, None)


if not any(isinstance(finder, _AliasFinder) for finder in sys.meta_path):
    sys.meta_path.append(_AliasFinder())
