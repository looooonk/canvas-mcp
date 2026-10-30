"""Decode a single untrusted image/PDF page with no credential environment."""

import io
import math
import resource
import sys
import warnings

from PIL import Image, ImageOps


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    Image.MAX_IMAGE_PIXELS = 25_000_000
    warnings.simplefilter("error", Image.DecompressionBombWarning)
    body = sys.stdin.buffer.read(25 * 1024 * 1024 + 1)
    if len(body) > 25 * 1024 * 1024:
        raise ValueError
    page_number = int(sys.argv[1])
    if body.startswith(b"%PDF-"):
        import pypdfium2 as pdfium

        with pdfium.PdfDocument(body) as document:
            if not 1 <= page_number <= len(document) <= 300:
                raise ValueError
            page = document[page_number - 1]
            width, height = page.get_size()
            if not all(math.isfinite(n) and n > 0 for n in (width, height)):
                raise ValueError
            bitmap = page.render(scale=min(2, 2000 / max(width, height)))
            image = bitmap.to_pil().convert("RGB")
            image.save(sys.stdout.buffer, format="PNG")
            bitmap.close()
            page.close()
    else:
        if page_number != 1:
            raise ValueError
        with Image.open(io.BytesIO(body)) as original:
            image = ImageOps.exif_transpose(original).convert("RGB")
            image.thumbnail((2000, 2000))
            image.save(sys.stdout.buffer, format="PNG")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit(1) from None
