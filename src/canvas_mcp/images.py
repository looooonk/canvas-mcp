import asyncio
import os
import sys
from pathlib import Path

import psutil

from canvas_mcp.catalog import CanvasError


async def render_image(body, page=1):
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(Path(__file__).with_name("image_worker.py")),
        str(page),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        env={"PATH": os.defpath},
    )

    async def monitor():
        try:
            worker = psutil.Process(process.pid)
        except psutil.NoSuchProcess:
            return
        while process.returncode is None:
            try:
                if worker.memory_info().rss > 512 * 1024 * 1024:
                    process.kill()
                    return
            except psutil.NoSuchProcess:
                return
            except psutil.Error:
                process.kill()
                return
            await asyncio.sleep(0.1)

    watcher = asyncio.create_task(monitor())
    try:
        output, _ = await asyncio.wait_for(process.communicate(body), timeout=25)
    except TimeoutError:
        raise CanvasError("Extraction exceeded its time limit.", code="extraction_error") from None
    finally:
        watcher.cancel()
        await asyncio.gather(watcher, return_exceptions=True)
        if process.returncode is None:
            process.kill()
            await process.wait()
    if (
        process.returncode
        or not output.startswith(b"\x89PNG\r\n\x1a\n")
        or len(output) > 16 * 1024 * 1024
    ):
        raise CanvasError(
            "Image/PDF page decoding failed, page is out of range, or limits exceeded.",
            code="extraction_error",
        )
    return output
