"""Run the isolated Vben browser smoke server with the project virtualenv."""

from __future__ import annotations

import os
from pathlib import Path
import sys


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(project_root))
    os.environ["VIDEO_PROVIDER"] = "mock"
    os.environ["DATABASE_PATH"] = str(project_root / "output" / "vben-smoke.db")

    # Configuration must be fixed before importing any backend module.
    import uvicorn
    from fastapi.responses import FileResponse
    from fastapi.routing import APIRoute

    from backend.main import app

    def demo_video() -> FileResponse:
        return FileResponse(
            project_root / "public" / "assets" / "demo-loop.mp4",
            media_type="video/mp4",
        )

    # This smoke-only fixture takes precedence over the production SPA mount.
    app.router.routes.insert(
        0,
        APIRoute(
            "/assets/demo-loop.mp4",
            demo_video,
            methods=["GET", "HEAD"],
            include_in_schema=False,
        ),
    )
    uvicorn.run(app, host="127.0.0.1", port=4174)


if __name__ == "__main__":
    main()
