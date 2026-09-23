import io
import zipfile

import pytest

from canvas_mcp.catalog import CanvasError
from canvas_mcp.content import extract_text, html_text, text_slice
from canvas_mcp.files import download_url

BASE = "https://canvas.example.edu"


def test_html_keeps_links_and_removes_scripts():
    text = html_text('<p>Read <a href="/files/1">notes</a></p><script>bad()</script>')
    assert "notes" in text and "/files/1" in text and "bad" not in text


def test_text_chunks_can_be_reassembled():
    assert text_slice("abcdef", 0, 3) == {
        "text": "abc",
        "offset": 0,
        "total_chars": 6,
        "next_offset": 3,
    }
    assert text_slice("abcdef", 3, 3)["next_offset"] is None


def test_office_document_extracts_paragraphs():
    file = io.BytesIO()
    with zipfile.ZipFile(file, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="urn:word"><w:p><w:r><w:t>Notes</w:t></w:r></w:p></w:document>',
        )
    text, warning = extract_text(file.getvalue(), "notes.docx", "application/octet-stream")
    assert text == "Notes" and warning


@pytest.mark.parametrize(
    "url",
    [BASE + "/files/1/download", BASE + "/files/1/download?preview=0&download_frd=0&verifier=abc"],
)
def test_file_requests_force_preview(url):
    result, auth = download_url(url, BASE, "1")
    assert auth and "preview=1" in result and "download_frd=1" in result


@pytest.mark.parametrize(
    "url",
    [
        "http://canvas.example.edu/files/1/download",
        "https://evil.example/files/1/download",
        "https://bucket.amazonaws.com.evil.example/file",
        "https://user:secret@bucket.s3.amazonaws.com/file",
        BASE + "/api/v1/courses/1/student_view_student",
        BASE + "/files/2/download",
        BASE + "/files/1/download?module_item_id=3",
        BASE + "/files/1/download?as_user_id=3",
        "https://x.instructure.com/api/v1/courses",
    ],
)
def test_unsafe_file_urls_blocked(url):
    with pytest.raises(CanvasError):
        download_url(url, BASE, "1")


def test_storage_never_receives_canvas_auth():
    _, auth = download_url("https://bucket.s3.amazonaws.com/file?signature=secret", BASE, "1")
    assert not auth


def test_no_text_extraction_for_binary_or_invalid_office_files():
    with pytest.raises(CanvasError):
        extract_text(b"binary", "movie.mp4", "video/mp4")
    with pytest.raises(CanvasError):
        extract_text(b"binary", "notes.docx", "application/zip")


def test_canvas_file_domain_redirect_retains_preview_without_auth():
    url, auth = download_url(
        "https://a123.cluster377.canvas-user-content.com/files/1/download?sf_verifier=signed",
        BASE,
        "1",
    )
    assert "preview=1" in url and not auth
