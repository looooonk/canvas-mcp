import base64
import json

import httpx
import pytest

from canvas_mcp.catalog import OPERATIONS, CanvasError, path_for, query_for
from canvas_mcp.client import CanvasClient
from canvas_mcp.config import Settings

TOKEN = "test-secret-never-returned"


def make_client(handler):
    return CanvasClient(
        Settings("https://canvas.example.edu", TOKEN), transport=httpx.MockTransport(handler)
    )


@pytest.mark.parametrize("name", OPERATIONS)
def test_catalog_routes_have_safe_ids_and_queries(name):
    import re

    op = OPERATIONS[name]
    path = {key: "123" for key in re.findall(r"{(\w+)}", op["path"])}
    assert path_for(name, path).startswith(("/api/v1/", "/api/quiz/v1/"))
    assert not {"as_user_id", "access_token", "_method", "auto_mark_as_read"} & op["query"].keys()


@pytest.mark.parametrize(
    "value",
    ["../student_view_student", "12/3", "%2e%2e", "1?x=2", "1#x", True, "student_view_student"],
)
async def test_path_injection_never_reaches_network(value):
    def handler(request):
        pytest.fail("Unsafe request reached network")

    client = make_client(handler)
    with pytest.raises(CanvasError):
        await client.read("course", {"id": value})
    await client.close()


@pytest.mark.parametrize(
    "query",
    [
        {"_method": "POST"},
        {"as_user_id": "42"},
        {"access_token": "x"},
        {"auto_mark_as_read": True},
        {"include[]": {"x": "y"}},
        {"per_page": 101},
    ],
)
async def test_query_injection_never_reaches_network(query):
    client = make_client(lambda _: pytest.fail("Unsafe request reached network"))
    with pytest.raises(CanvasError):
        await client.read("conversations", query=query)
    await client.close()


async def test_conversation_is_not_marked_read_and_token_is_header_only():
    def handler(request):
        assert request.method == "GET"
        assert request.url.params["auto_mark_as_read"] == "false"
        assert request.headers["authorization"] == f"Bearer {TOKEN}"
        assert request.headers["accept"] == "application/json+canvas-string-ids"
        assert TOKEN not in str(request.url)
        return httpx.Response(200, json={"id": "9", "workflow_state": "unread"})

    client = make_client(handler)
    result = await client.read("conversation", {"id": "9"})
    assert result["data"]["workflow_state"] == "unread"
    assert TOKEN not in json.dumps(result)
    await client.close()


async def test_pagination_preserves_array_filters():
    requests = []

    def handler(request):
        requests.append(request)
        assert request.url.params.get_list("include[]") == ["term", "total_scores"]
        headers = {
            "link": (
                "<https://canvas.example.edu/api/v1/courses?include[]=term&include[]=total_scores"
                '&page=opaque-2&per_page=1>; rel="next"'
            )
        }
        return httpx.Response(
            200, json=[{"id": str(len(requests))}], headers=headers if len(requests) == 1 else {}
        )

    client = make_client(handler)
    first = await client.read(
        "courses", query={"include[]": ["term", "total_scores"], "per_page": 1}
    )
    second = await client.read("courses", cursor=first["pagination"]["next_cursor"])
    assert second["data"] == [{"id": "2"}]
    assert second["pagination"]["has_more"] is False
    assert requests[1].url.params["page"] == "opaque-2"
    await client.close()


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example/api/v1/courses?page=2",
        "http://canvas.example.edu/api/v1/courses?page=2",
        "https://canvas.example.edu/api/v1/courses/1/student_view_student?page=2",
        "https://canvas.example.edu/api/v1/courses?_method=DELETE",
        "https://canvas.example.edu/api/v1/courses?as_user_id=2",
    ],
)
async def test_unsafe_pagination_rejected(url):
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=[], headers={"link": f'<{url}>; rel="next"'})

    client = make_client(handler)
    with pytest.raises(CanvasError):
        await client.read("courses")
    assert len(requests) == 1
    await client.close()


async def test_forged_cursor_revalidated():
    client = make_client(lambda _: pytest.fail("Unsafe request reached network"))
    payload = {
        "operation": "conversation",
        "path": {"id": "1"},
        "query": {"auto_mark_as_read": True},
    }
    cursor = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    with pytest.raises(CanvasError):
        await client.read("conversation", {"id": "1"}, cursor=cursor)
    await client.close()


@pytest.mark.parametrize("status", [301, 302, 401, 403, 404, 500])
async def test_errors_do_not_expose_response_body_or_follow_redirects(status):
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(status, text=TOKEN, headers={"location": "https://evil.example"})

    client = make_client(handler)
    with pytest.raises(CanvasError) as error:
        await client.read("courses")
    assert TOKEN not in str(error.value)
    assert len(seen) == 1
    await client.close()


async def test_retry_429_and_503(monkeypatch):
    delays = []

    async def sleep(delay):
        delays.append(delay)

    monkeypatch.setattr("canvas_mcp.client.asyncio.sleep", sleep)
    statuses = iter([429, 503, 200])
    client = make_client(
        lambda _: httpx.Response(next(statuses), json=[], headers={"retry-after": "999"})
    )
    assert (await client.read("courses"))["data"] == []
    assert delays == [3, 3]
    await client.close()


@pytest.mark.parametrize(
    "url",
    [
        "http://canvas.example.edu",
        "https://user:pass@canvas.example.edu",
        "https://canvas.example.edu/api/v1",
        "https://canvas.example.edu?x=1",
    ],
)
def test_base_url_validation(url):
    with pytest.raises(ValueError):
        Settings(url, TOKEN)


def test_token_not_in_repr():
    assert TOKEN not in repr(Settings("https://canvas.example.edu", TOKEN))


def test_missing_required_query_and_wrong_scalar_types():
    with pytest.raises(CanvasError):
        query_for("announcements", {})
    with pytest.raises(CanvasError):
        query_for("announcements", {"context_codes[]": "course_1"})
    with pytest.raises(CanvasError):
        query_for("calendar_events", {"all_events": "maybe"})


async def test_compressed_canvas_response_is_decoded_once():
    import gzip

    client = make_client(
        lambda _: httpx.Response(
            200,
            content=gzip.compress(b'[{"id":"123"}]'),
            headers={"content-type": "application/json", "content-encoding": "gzip"},
        )
    )
    assert (await client.read("courses"))["data"] == [{"id": "123"}]
    await client.close()
