import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    base_url: str
    token: str = field(repr=False)

    def __post_init__(self):
        url = urlsplit(self.base_url)
        if (
            url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
            or url.path not in ("", "/")
        ):
            raise ValueError(
                "CANVAS_BASE_URL must be an HTTPS origin without a path or credentials."
            )
        if not self.token or any(c.isspace() for c in self.token):
            raise ValueError("CANVAS_API_TOKEN is missing or contains whitespace.")
        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))

    @classmethod
    def load(cls, env_file: Path):
        values = dotenv_values(env_file, interpolate=False)
        return cls(
            os.environ.get("CANVAS_BASE_URL") or values.get("CANVAS_BASE_URL") or "",
            os.environ.get("CANVAS_API_TOKEN") or values.get("CANVAS_API_TOKEN") or "",
        )
