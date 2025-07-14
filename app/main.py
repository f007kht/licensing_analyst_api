from fastapi import FastAPI, HTTPException
from app.gpt_connector import assemble_deal_profile
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class DealProfileRequest(BaseModel):
    nct_id: str
    sec_text: str
    sec_url: Optional[str] = "[SEC filing URL placeholder]"

@app.post("/assemble_deal_profile")
def handle_profile(req: DealProfileRequest):
    try:
        return assemble_deal_profile(req.nct_id, req.sec_text, req.sec_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
