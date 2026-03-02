"""Path and URL safety guards used by compatibility tests and adapters."""

from __future__ import annotations

from ipaddress import ip_address
from pathlib import Path
from urllib.parse import urlparse


class PathSecurityError(ValueError):
    """Raised when a path violates security constraints."""


class DownloadSecurityError(ValueError):
    """Raised when a remote URL is unsafe for downloading."""


def ensure_safe_relative_path(relative_path: str) -> str:
    """Validate and normalize a user-provided relative path."""
    value = (relative_path or "").strip()
    if not value:
        raise PathSecurityError("相对路径不能为空")
    if value.startswith(("/", "\\")):
        raise PathSecurityError("不允许绝对路径")

    normalized = Path(value)
    if normalized.is_absolute():
        raise PathSecurityError("不允许绝对路径")

    parts = normalized.parts
    if any(part == ".." for part in parts):
        raise PathSecurityError("不允许路径穿越")

    return normalized.as_posix()


def ensure_within_roots(path: str, roots: list[str]) -> Path:
    """Ensure target path is inside one of the allowed root directories."""
    if not roots:
        raise PathSecurityError("未配置允许访问的根目录")

    target = Path(path).resolve()
    allowed_roots = [Path(root).resolve() for root in roots]

    for root in allowed_roots:
        if target == root:
            return target
        try:
            target.relative_to(root)
            return target
        except ValueError:
            continue
    raise PathSecurityError(f"路径不在允许目录内: {target}")


def _is_unsafe_host(hostname: str) -> bool:
    host = (hostname or "").strip().lower()
    if not host:
        return True
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True

    try:
        ip = ip_address(host)
    except ValueError:
        # Domain name: keep simple allow-list behavior (https required elsewhere).
        return False

    return any(
        [
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_reserved,
            ip.is_multicast,
            ip.is_unspecified,
        ]
    )


def validate_remote_url(url: str) -> str:
    """Validate remote URL for secure file download."""
    raw = (url or "").strip()
    parsed = urlparse(raw)

    if parsed.scheme.lower() != "https":
        raise DownloadSecurityError("仅允许 HTTPS 下载地址")
    if _is_unsafe_host(parsed.hostname or ""):
        raise DownloadSecurityError("不允许本地或内网地址")
    if not parsed.path:
        raise DownloadSecurityError("下载地址缺少路径")

    return raw


__all__ = [
    "PathSecurityError",
    "DownloadSecurityError",
    "ensure_safe_relative_path",
    "ensure_within_roots",
    "validate_remote_url",
]

