import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field


app = FastAPI(
    title="IPC Hermes Bridge API",
    version="0.1.1",
    description="Bridge API để IPC Land gửi request research KCN."
)

API_KEY = os.getenv("IPC_HERMES_API_KEY", "")


class ResearchKCNRequest(BaseModel):
    kcn_name: str = Field(..., examples=["VSIP Quảng Ngãi"])
    source_url: Optional[str] = Field(None)
    note: Optional[str] = Field(None)
    requested_by: Optional[str] = Field("admin")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def verify_auth(authorization: Optional[str]):
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Server missing IPC_HERMES_API_KEY")

    expected = f"Bearer {API_KEY}"

    if authorization != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


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
async def research_kcn(
    payload: ResearchKCNRequest,
    authorization: Optional[str] = Header(None)
):
    verify_auth(authorization)

    kcn_name = payload.kcn_name

    result = {
        "status": "completed",
        "type": "kcn_research",
        "requested_by": payload.requested_by,
        "created_at": now_iso(),
        "result": {
            "type": "kcn_research",
            "kcn_name": kcn_name,
            "source_url": payload.source_url,
            "note": payload.note,
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
    }

    return result
