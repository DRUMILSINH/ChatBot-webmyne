import ipaddress
import re
import socket
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError


PII_PATTERNS = [
    re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w{2,}\b"),
    re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\d{10,12})\b"),
]

SENSITIVE_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
]

PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"reveal\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"developer\s+message", re.IGNORECASE),
]


def sanitize_text(text: str, max_chars: int = 4000) -> str:
    if text is None:
        return ""
    normalized = str(text).replace("\x00", " ").strip()
    return normalized[:max_chars]


def redact_pii(text: str) -> str:
    output = text
    for pattern in PII_PATTERNS:
        output = pattern.sub("[REDACTED]", output)
    return output


def sanitize_output(text: str) -> str:
    return redact_pii(text).strip()


def violates_input_policy(text: str) -> tuple[bool, str]:
    if not text:
        return True, "empty_input"
    if len(text) > 4000:
        return True, "input_too_long"
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(text):
            return True, "prompt_injection_pattern"
    return False, ""


def violates_output_policy(text: str) -> tuple[bool, str]:
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            return True, "sensitive_pattern_detected"
    return False, ""


def safe_block_message() -> str:
    return getattr(
        settings,
        "SAFE_BLOCK_MESSAGE",
        "I cannot help with that request because it violates data safety policy.",
    )


def _host_is_private_or_loopback(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local
    except ValueError:
        try:
            infos = socket.getaddrinfo(host, None)
            for info in infos:
                ip = ipaddress.ip_address(info[4][0])
                if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                    return True
        except socket.gaierror:
            return True
    return False


def _allowed_domains_for_vector(vector_id: str) -> tuple[bool, list[str]]:
    allowlist = getattr(settings, "CRAWL_DOMAIN_ALLOWLIST", {}) or {}
    if not allowlist:
        return False, []

    allowed = allowlist.get(vector_id, allowlist.get("*", []))
    return True, [domain.lower().strip() for domain in allowed if domain and domain.strip()]


def _host_matches_allowlist(host: str, allowed_domains: list[str]) -> bool:
    lowered = (host or "").lower().strip(".")
    for domain in allowed_domains:
        if lowered == domain or lowered.endswith(f".{domain}"):
            return True
    return False


def _resolve_ips(host: str) -> list[ipaddress._BaseAddress]:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise PermissionDenied(f"DNS lookup failed for host '{host}': {exc}")

    ips = []
    for info in infos:
        try:
            ips.append(ipaddress.ip_address(info[4][0]))
        except Exception:
            continue
    if not ips:
        raise PermissionDenied(f"No IP addresses resolved for host '{host}'.")
    return ips


def _ensure_public_host(host: str) -> None:
    for ip in _resolve_ips(host):
        if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
            raise PermissionDenied(f"Host '{host}' resolves to private/internal IP '{ip}'.")


def _validate_redirect_chain(url: str, allowed_domains: list[str]) -> None:
    if not getattr(settings, "CRAWL_VALIDATE_REDIRECTS", True):
        return

    response = None
    try:
        response = requests.get(
            url,
            timeout=(4, 8),
            allow_redirects=True,
            stream=True,
            headers={"User-Agent": "chatbot-crawler-validator/1.0"},
        )
    except requests.RequestException as exc:
        raise PermissionDenied(f"Failed to validate redirect chain: {exc}")
    finally:
        try:
            response.close()
        except Exception:
            pass

    chain = list(response.history) + [response]
    for hop in chain:
        hop_url = hop.url
        parsed = urlparse(hop_url)
        host = parsed.hostname or ""
        if parsed.scheme not in {"http", "https"}:
            raise PermissionDenied("Redirect chain contains non-http(s) scheme.")
        if allowed_domains and not _host_matches_allowlist(host, allowed_domains):
            raise PermissionDenied(f"Redirect chain escaped allowlist via host '{host}'.")
        _ensure_public_host(host)


def validate_crawl_url(url: str, vector_id: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValidationError("Only valid http/https URLs are allowed.")

    if parsed.username or parsed.password:
        raise PermissionDenied("URLs with embedded credentials are not allowed.")

    _ensure_public_host(parsed.hostname)

    has_allowlist, allowed = _allowed_domains_for_vector(vector_id)
    require_allowlist = bool(getattr(settings, "CRAWL_REQUIRE_ALLOWLIST", False))
    if require_allowlist and not has_allowlist:
        raise PermissionDenied("Crawl allowlist is required but not configured.")
    if has_allowlist and not allowed:
        raise PermissionDenied("No crawl allowlist configured for this vector_id.")

    host = parsed.hostname.lower().strip(".")
    if has_allowlist and not _host_matches_allowlist(host, allowed):
        raise PermissionDenied("Target domain is not allowlisted for this tenant.")

    _validate_redirect_chain(url, allowed)


def sanitize_debug_text(text: str, limit: int = 300) -> str:
    truncated = redact_pii((text or "").strip()[:limit])
    truncated = re.sub(r"\b\d{6,}\b", "[REDACTED_NUM]", truncated)
    return truncated


def sanitize_debug_payload(payload: dict) -> dict:
    safe = dict(payload or {})
    chunks = []
    for doc in safe.get("retrieved_chunks", []) or []:
        item = dict(doc)
        item["content"] = sanitize_debug_text(str(item.get("content", "")), 300)
        chunks.append(item)
    safe["retrieved_chunks"] = chunks

    retrieved = []
    for doc in safe.get("retrieved_documents", []) or safe["retrieved_chunks"]:
        item = dict(doc)
        item["content"] = sanitize_debug_text(str(item.get("content", "")), 300)
        retrieved.append(item)
    safe["retrieved_documents"] = retrieved

    src = []
    for doc in safe.get("sources", []) or []:
        item = dict(doc)
        item["content"] = sanitize_debug_text(str(item.get("content", "")), 300)
        src.append(item)
    safe["sources"] = src
    return safe
