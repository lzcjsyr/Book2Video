"""FastAPI app for web-side access to the same core business logic."""

from fastapi import FastAPI

from api.routers import jobs, pipeline


app = FastAPI(title="AIGC Video Backend", version="0.1.0")

app.include_router(pipeline.router)
app.include_router(jobs.router)


@app.get("/healthz")
def healthz():
    return {"ok": True}

