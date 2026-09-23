import asyncio
import re
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit, urlunsplit

import httpx

from canvas_mcp.catalog import CanvasError
from canvas_mcp.client import CanvasClient
from canvas_mcp.content import MAX_FILE_BYTES

STORAGE_SUFFIXES = (
    ".instructure.com",
    ".instructure-uploads.com",
    ".canvas-user-content.com",
    ".amazonaws.com",
    ".cloudfront.net",
    ".inscloudgate.net",
)


def download_url(url: str, base_url: str, file_id: str) -> tuple[str, bool]:
    target, base = urlsplit(url), urlsplit(base_url)
    if (
        target.scheme != "https"
        or not target.hostname
        or target.username
        or target.password
        or target.fragment
        or target.port not in (None, 443)
    ):
        raise CanvasError("Unsafe file download URL was blocked.")
    same_origin = (target.scheme, target.netloc) == (base.scheme, base.netloc)
    canvas_file_host = same_origin or target.hostname.endswith(
        (".canvas-user-content.com", ".instructure.com")
    )
    if canvas_file_host:
        if not re.fullmatch(rf"/files/(?:[0-9]+~)?{re.escape(file_id)}/download", target.path):
            raise CanvasError("Unexpected Canvas file redirect was blocked.")
        query = parse_qs(target.query, max_num_fields=30)
        if set(query) - {"verifier", "sf_verifier", "download_frd", "preview", "download"}:
            raise CanvasError("Unexpected Canvas file parameters were blocked.")
        # Canvas skips context_module_action in send_stored_file when preview is set.
        query.update(preview=["1"], download_frd=["1"])
        return urlunsplit(target._replace(query=urlencode(query, doseq=True))), same_origin
    if not any(target.hostname.endswith(suffix) for suffix in STORAGE_SUFFIXES):
        raise CanvasError("File storage host is not allowlisted. Use the file's Canvas link.")
    if target.path.startswith(("/api/", "/login", "/logout")):
        raise CanvasError("Unexpected file storage route was blocked.")
    return url, False


async def read_file(client: CanvasClient, file_id: str) -> tuple[dict, bytes]:
    metadata = (await client.read("file", {"id": file_id}))["data"]
    if metadata.get("locked_for_user"):
        raise CanvasError("Canvas reports this file is locked for you.")
    if metadata.get("size", 0) > MAX_FILE_BYTES:
        raise CanvasError("File exceeds the 25 MiB download limit.")
    if not re.fullmatch(r"[0-9]{1,30}", file_id):
        raise CanvasError("file_id must be numeric.")
    url = metadata.get("url", "")
    try:
        # A separate session prevents API cookies from being sent to storage.
        async with (
            asyncio.timeout(45),
            client.slots,
            httpx.AsyncClient(follow_redirects=False, timeout=20, trust_env=False) as http,
        ):
            for _ in range(6):
                url, authenticated = download_url(url, client.settings.base_url, file_id)
                headers = (
                    {"Authorization": f"Bearer {client.settings.token}"} if authenticated else {}
                )
                async with http.stream("GET", url, headers=headers) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location")
                        if not location:
                            raise CanvasError("Canvas file redirect was missing its destination.")
                        url = urljoin(url, location)
                        http.cookies.clear()
                        continue
                    if response.status_code != 200:
                        raise CanvasError(f"File download returned HTTP {response.status_code}.")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_FILE_BYTES:
                            raise CanvasError("File exceeds the 25 MiB download limit.")
                    return metadata, bytes(body)
            raise CanvasError("Too many file download redirects.")
    except (httpx.RequestError, TimeoutError):
        raise CanvasError("Could not download the Canvas file securely. Try again later.") from None
