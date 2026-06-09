import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from prompts import build_prompt

load_dotenv()

app = FastAPI(title="CryptoWrite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


class GenerateRequest(BaseModel):
    raw_material: str
    content_types: list[str] = ["wechat", "twitter"]
    style: str = "kol"
    language: str = "zh"


class GenerateResponse(BaseModel):
    content: str


@app.get("/")
async def serve_index():
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "CryptoWrite API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    if not req.raw_material.strip():
        raise HTTPException(status_code=400, detail="raw_material is required")

    valid_styles = {"analyst", "kol", "official"}
    if req.style not in valid_styles:
        raise HTTPException(status_code=400, detail=f"style must be one of {valid_styles}")

    valid_types = {"wechat", "twitter"}
    for ct in req.content_types:
        if ct not in valid_types:
            raise HTTPException(status_code=400, detail=f"content_type must be one of {valid_types}")

    system_prompt, user_prompt = build_prompt(
        raw_material=req.raw_material,
        content_types=req.content_types,
        style=req.style,
        language=req.language,
    )

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return GenerateResponse(content=message.content[0].text)
