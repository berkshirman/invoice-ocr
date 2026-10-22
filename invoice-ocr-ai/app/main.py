import multiprocessing
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import get_settings
from app.routers import health, invoices, settings as settings_router
from app.rate_limit import limiter

settings = get_settings()


class SPAStaticFiles(StaticFiles):
    """Serve the built frontend and fall back to index.html for client routes.

    Unknown /api/* paths keep returning 404 instead of the SPA shell.
    """

    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and not path.lstrip("/").startswith("api/"):
                return await super().get_response("index.html", scope)
            raise


def _static_dir() -> Path:
    """Locate the frontend files in dev and in a PyInstaller onefile binary."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / "static"

app = FastAPI(
    title="发票管理系统",
    description="Invoice Manager API - 发票上传、解析、管理系统",
    version="1.0.0",
)

# Add rate limiter to app state
app.state.limiter = limiter


# Custom rate limit exceeded handler with Chinese message
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": f"请求过于频繁，请稍后再试。限制: {exc.detail}"}
    )


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:15173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])

# Serve the built frontend at "/" (registered last so /api and /docs win).
_static = _static_dir()
if _static.is_dir():
    app.mount("/", SPAStaticFiles(directory=str(_static), html=True), name="static")


# @app.on_event("startup")
# async def startup():
#     from app.database import engine, Base
#     async with engine.begin() as conn:
#         # await conn.run_sync(Base.metadata.create_all)
#         await conn.run_sync(Base.metadata.create_all)


def main():
    # Required on Windows for frozen executables that spawn subprocesses.
    multiprocessing.freeze_support()
    # Pass the app object directly and disable reload: a PyInstaller onefile
    # binary cannot re-import "app.main:app" in a spawned subprocess.
    # For development use `uvicorn app.main:app --reload` instead.
    uvicorn.run(app, host="0.0.0.0", port=18080, workers=1)


if __name__ == "__main__":
    main()
