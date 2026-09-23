import asyncio
import base64
import json
from urllib.parse import parse_qs, urlsplit

import httpx

from canvas_mcp.catalog import CanvasError, operation, path_for, query_for
from canvas_mcp.config import Settings

MAX_API_BYTES = 8 * 1024 * 1024


class CanvasClient:
    def __init__(self, settings: Settings, *, transport=None):
        self.settings = settings
        self.http = httpx.AsyncClient(
            timeout=httpx.Timeout(20, connect=10),
            follow_redirects=False,
            trust_env=False,
            transport=transport,
            headers={"User-Agent": "canvas-mcp/0.1 (local read-only)"},
        )
        self.slots = asyncio.Semaphore(4)

    async def close(self):
        await self.http.aclose()

    async def _get_json(self, path: str, pairs: list[tuple[str, str]]) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self.settings.token}",
            "Accept": "application/json+canvas-string-ids",
        }
        async with self.slots:
            for attempt in range(3):
                try:
                    async with self.http.stream(
                        "GET", self.settings.base_url + path, params=pairs, headers=headers
                    ) as response:
                        if response.status_code in (429, 502, 503, 504) and attempt < 2:
                            retry = response.headers.get("retry-after", "")
                            delay = min(float(retry), 3) if retry.isdecimal() else 0.5 * 2**attempt
                            await asyncio.sleep(delay)
                            continue
                        messages = {
                            400: "Canvas rejected parameters or the operation is not applicable.",
                            401: "Canvas authentication failed. Check the local API token.",
                            403: "Canvas denied access. Feature may be unavailable to students.",
                            404: "Canvas resource not found or not available to this account.",
                            429: "Canvas rate limit reached. Try again later.",
                        }
                        if response.status_code != 200:
                            raise CanvasError(
                                messages.get(
                                    response.status_code,
                                    f"Canvas HTTP {response.status_code}; redirects blocked.",
                                ),
                                code="http_error",
                                http_status=response.status_code,
                            )
                        if "json" not in response.headers.get("content-type", "").lower():
                            raise CanvasError(
                                "Canvas returned a non-JSON response. Check the Canvas base URL."
                            )
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk)
                            if len(body) > MAX_API_BYTES:
                                raise CanvasError(
                                    "Canvas response is too large. Request fewer items."
                                )
                        return httpx.Response(
                            response.status_code,
                            headers={
                                k: v
                                for k, v in response.headers.items()
                                if k not in {"content-encoding", "content-length"}
                            },
                            content=bytes(body),
                            request=response.request,
                        )
                except httpx.RequestError:
                    if attempt == 2:
                        raise CanvasError(
                            "Cannot reach Canvas securely. Check your connection and URL.",
                            code="connection_error",
                        ) from None
                    await asyncio.sleep(0.5 * 2**attempt)
        raise CanvasError("Canvas request failed.")

    def _next_cursor(self, response: httpx.Response, name: str, path: dict) -> str | None:
        link = response.links.get("next", {}).get("url")
        if not link:
            return None
        target = urlsplit(link)
        origin = urlsplit(self.settings.base_url)
        if (
            (target.scheme, target.netloc) != (origin.scheme, origin.netloc)
            or target.path != urlsplit(str(response.request.url)).path
            or target.fragment
        ):
            raise CanvasError("Canvas supplied an unsafe pagination link; it was not followed.")
        parsed = parse_qs(target.query, keep_blank_values=True, max_num_fields=500)
        query = {}
        fixed = operation(name).get("fixed_query", {})
        for key, values in parsed.items():
            if key in fixed:
                if values != [str(fixed[key]).lower()]:
                    raise CanvasError(
                        "Canvas supplied a pagination link that changes read-only settings."
                    )
                continue
            if not key.endswith("[]") and len(values) != 1:
                raise CanvasError("Canvas supplied ambiguous pagination parameters.")
            query[key] = values if key.endswith("[]") else values[0]
        query_for(name, query)
        return base64.urlsafe_b64encode(
            json.dumps(
                {"operation": name, "path": path, "query": query}, separators=(",", ":")
            ).encode()
        ).decode()

    async def read(
        self,
        name: str,
        path: dict | None = None,
        query: dict | None = None,
        cursor: str | None = None,
    ) -> dict:
        path = path or {}
        query = query or {}
        if cursor:
            if query:
                raise CanvasError(
                    "When resuming a cursor, omit query and keep the same operation/path."
                )
            try:
                if len(cursor) > 32768:
                    raise ValueError
                payload = json.loads(base64.b64decode(cursor, altchars=b"-_", validate=True))
                if payload["operation"] != name or payload["path"] != path:
                    raise ValueError
                query = payload["query"]
                if not isinstance(query, dict):
                    raise ValueError
            except (ValueError, TypeError, KeyError):
                raise CanvasError("Invalid cursor for this operation/path.") from None
        endpoint = path_for(name, path)
        pairs = query_for(name, query)
        try:
            async with asyncio.timeout(45):
                response = await self._get_json(endpoint, pairs)
        except TimeoutError:
            raise CanvasError("Canvas request timed out. Try again with a smaller page.") from None
        try:
            data = response.json()
        except ValueError:
            raise CanvasError("Canvas returned invalid JSON.") from None
        cursor = self._next_cursor(response, name, path)
        return {
            "operation": name,
            "data": data,
            "source_url": self.settings.base_url + endpoint,
            "pagination": {"has_more": cursor is not None, "next_cursor": cursor},
        }
