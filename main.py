import os
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import FastAPI, BackgroundTasks, Header, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(
    title="IPC Hermes Bridge API",
    version="0.1.0",
    description="Bridge API để IPC Land gửi job research KCN."
)

API_KEY = os.getenv("IPC_HERMES_API_KEY", "")

JOBS: Dict[str, Dict[str, Any]] = {}


class ResearchKCNRequest(BaseModel):
    kcn_name: str = Field(..., examples=["VSIP Quảng Ngãi"])
    source_url: Optional[str] = Field(None)
    note: Optional[str] = Field(None)
    callback_url: Optional[str] = Field(None)
    requested_by: Optional[str] = Field("admin")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def verify_auth(authorization: Optional[str]):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Server missing IPC_HERMES_API_KEY")

    expected = f"Bearer {API_KEY}"

    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


async def fake_research_kcn(job_id: str, payload: ResearchKCNRequest):
    JOBS[job_id]["status"] = "running"
    JOBS[job_id]["updated_at"] = now_iso()

    await asyncio.sleep(3)

    kcn_name = payload.kcn_name

    result = {
        "type": "kcn_research",
        "kcn_name": kcn_name,
        "source_url": payload.source_url,
        "summary": f"Bản nháp dữ liệu cho {kcn_name}. Cần admin IPC Land kiểm tra trước khi lưu DB.",
        "data": {
            "name": kcn_name,
            "province": None,
            "scale_ha": None,
            "developer": None,
            "land_lease_price": None,
            "available_area": None,
            "infrastructure": {
                "power": None,
                "water": None,
                "wastewater_treatment": None
            },
            "logistics": {
                "nearest_port": None,
                "nearest_airport": None,
                "highway_connection": None
            },
            "suitable_industries": []
        },
        "missing_fields": [
            "province",
            "scale_ha",
            "developer",
            "land_lease_price",
            "available_area",
            "nearest_port",
            "nearest_airport"
        ],
        "confidence_score": 0.30,
        "sources": []
    }

    JOBS[job_id]["status"] = "completed"
    JOBS[job_id]["result"] = result
    JOBS[job_id]["updated_at"] = now_iso()


@app.get("/")
def root():
    return {
        "ok": True,
        "service": "ipc-hermes-bridge",
        "message": "IPC Hermes Bridge API is running"
    }


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "ipc-hermes-bridge",
        "time": now_iso()
    }


@app.post("/api/v1/research/kcn")
async def create_research_kcn_job(
    payload: ResearchKCNRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    verify_auth(authorization)

    job_id = f"job_{uuid.uuid4().hex[:12]}"

    JOBS[job_id] = {
        "job_id": job_id,
        "type": "research_kcn",
        "status": "queued",
        "request": payload.model_dump(),
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "result": None
    }

    background_tasks.add_task(fake_research_kcn, job_id, payload)

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Research KCN job accepted"
    }


@app.get("/api/v1/jobs/{job_id}")
def get_job(
    job_id: str,
    authorization: Optional[str] = Header(None)
):
    verify_auth(authorization)

    job = JOBS.get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job
