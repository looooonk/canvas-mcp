import io
from types import SimpleNamespace

import httpx
import pytest
from PIL import Image
from pypdf import PdfWriter

from canvas_mcp.catalog import CanvasError, path_for
from canvas_mcp.changes import CanvasChanges
from canvas_mcp.client import CanvasClient
from canvas_mcp.config import Settings
from canvas_mcp.images import render_image


async def test_render_image_and_selected_pdf_page():
    output = io.BytesIO()
    Image.new("RGB", (2500, 1000), "red").save(output, "PNG")
    image = Image.open(io.BytesIO(await render_image(output.getvalue())))
    assert image.size == (2000, 800)
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=400)
    writer.add_blank_page(width=600, height=300)
    pdf = io.BytesIO()
    writer.write(pdf)
    page = Image.open(io.BytesIO(await render_image(pdf.getvalue(), 2)))
    assert page.width == 2 * page.height
    with pytest.raises(CanvasError, match="out of range"):
        await render_image(pdf.getvalue(), 3)
    with pytest.raises(CanvasError):
        await render_image(b"not an image")


@pytest.mark.parametrize(
    "status,code",
    [(403, "permission_denied"), (404, "not_found_or_unavailable"), (400, "invalid_parameters")],
)
async def test_pages_upstream_errors_are_not_schema_errors(status, code):
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(status, json={"errors": [{"message": "secret"}]})

    c = CanvasClient(
        Settings("https://example.edu", "token"), transport=httpx.MockTransport(handle)
    )
    with pytest.raises(CanvasError) as error:
        await c.read("pages", {"course_id": "1"}, {"per_page": 1})
    assert error.value.code == code and error.value.http_status == status
    assert "secret" not in str(error.value)
    assert calls[0].method == "GET" and calls[0].url.path == "/api/v1/courses/1/pages"
    await c.close()


def test_unambiguous_page_id():
    assert path_for("page", {"course_id": 1, "url_or_id": "page_id:7"}).endswith("/page_id%3A7")


async def test_feed_submission_fields_and_no_incremental_filter_gap():
    class Client:
        settings = SimpleNamespace(base_url="https://example.edu")

        async def read(self, name, path, query, cursor):
            assert name == "student_submissions" and query["student_ids[]"] == ["self"]
            assert "graded_since" not in query and "submitted_since" not in query
            assert "submission_comments" in query["include[]"]
            return {
                "data": [
                    {
                        "id": 7,
                        "assignment_id": 2,
                        "score": None,
                        "submission_comments": [{"comment": "feedback"}],
                    }
                ],
                "pagination": {"next_cursor": None},
            }

    records, more = await CanvasChanges().collect(
        Client(), "1", {"source": "student_submissions", "cursor": None}
    )
    assert records[0]["fields"]["score"] is None and more == []
    assert records[0]["source_url"].endswith("/assignments/2/submissions/self")
