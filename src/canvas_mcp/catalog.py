import json
import re
from importlib.resources import files
from urllib.parse import quote

OPERATIONS = json.loads(files("canvas_mcp").joinpath("operations.json").read_text())


class CanvasError(ValueError):
    """A safe, actionable error that may be shown to an MCP client."""


def operation(name: str) -> dict:
    if name not in OPERATIONS:
        raise CanvasError(
            "Unknown operation. Use canvas_find_operations to discover allowed reads."
        )
    return OPERATIONS[name]


def path_for(name: str, path: dict) -> str:
    template = operation(name)["path"]
    expected = set(re.findall(r"{(\w+)}", template))
    if set(path) != expected:
        raise CanvasError(
            f"Path parameters must be exactly: {', '.join(sorted(expected)) or 'none'}."
        )
    encoded = {}
    for key, value in path.items():
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise CanvasError(f"{key} must be an ID or slug string.")
        value = str(value)
        is_self = value == "self" and (
            key == "user_id"
            or (key == "id" and name in {"user", "user_colors", "graded_submissions"})
        )
        is_slug = key == "url_or_id" and re.fullmatch(r"[\w-]{1,255}", value)
        if not (re.fullmatch(r"[0-9]{1,30}", value) or is_self or is_slug):
            raise CanvasError(f"Invalid {key}; use a numeric ID, 'self' for users, or a page slug.")
        encoded[key] = quote(value, safe="")
    return template.format(**encoded)


def query_for(name: str, query: dict) -> list[tuple[str, str]]:
    op = operation(name)
    specs = op["query"] | {
        "page": {"type": "string", "required": False},
        "per_page": {"type": "integer", "required": False},
    }
    unknown = set(query) - set(specs)
    if unknown:
        raise CanvasError("Unsupported query parameter(s). Use canvas_describe_operation.")
    missing = [k for k, v in specs.items() if v["required"] and k not in query]
    if missing:
        raise CanvasError(f"Required query parameters: {', '.join(missing)}.")
    pairs = []
    for key, value in (dict(per_page=50) | query).items():
        spec = specs[key]
        if key.endswith("[]"):
            if not isinstance(value, list) or not value or len(value) > 100:
                raise CanvasError(f"{key} must be a nonempty array with at most 100 values.")
            values = value
        else:
            if isinstance(value, (dict, list)):
                raise CanvasError(f"{key} must be a scalar value.")
            values = [value]
        for item in values:
            if item is None or not isinstance(item, (str, int, float, bool)):
                raise CanvasError(f"Invalid value for {key}.")
            text = str(item).lower() if isinstance(item, bool) else str(item)
            if len(text) > 4096 or any(ord(c) < 32 for c in text):
                raise CanvasError(f"Invalid value for {key}.")
            if spec["type"] == "boolean" and text not in ("true", "false"):
                raise CanvasError(f"{key} must be true or false.")
            if spec["type"] == "integer" and not re.fullmatch(r"[0-9]{1,30}", text):
                raise CanvasError(f"{key} must be a nonnegative integer.")
            if key == "per_page" and not 1 <= int(text) <= 100:
                raise CanvasError("per_page must be between 1 and 100.")
            pairs.append((key, text))
    for key, value in op.get("fixed_query", {}).items():
        pairs.append((key, str(value).lower()))
    return pairs


def describe(name: str) -> dict:
    op = operation(name)
    return {
        "operation": name,
        **op,
        "path_parameters": re.findall(r"{(\w+)}", op["path"]),
        "pagination": (
            "query.per_page is 1-100 (default 50). Reuse next_cursor with the same operation/path."
        ),
    }
