"""Helpers for preserving package-level APIs without eager import chains."""

from collections.abc import Callable, Mapping, MutableMapping
from importlib import import_module
from typing import Any

ExportMap = Mapping[str, tuple[str, str]]


def lazy_getattr(
    module_name: str,
    namespace: MutableMapping[str, Any],
    exports: ExportMap,
) -> Callable[[str], Any]:
    def __getattr__(name: str) -> Any:
        try:
            target_module, attribute_name = exports[name]
        except KeyError as exc:
            raise AttributeError(
                f"module {module_name!r} has no attribute {name!r}"
            ) from exc
        value = getattr(import_module(target_module), attribute_name)
        namespace[name] = value
        return value

    return __getattr__


def lazy_dir(
    namespace: Mapping[str, Any], public_names: list[str]
) -> Callable[[], list[str]]:
    return lambda: sorted({*namespace, *public_names})
