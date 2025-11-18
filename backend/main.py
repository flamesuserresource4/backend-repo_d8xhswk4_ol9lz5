from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import os

from database import db, create_document, get_documents, database_url, database_name
import importlib

app = FastAPI(title="Liteweb Agency API", version="1.0.0")

# CORS setup for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Basic root endpoint
@app.get("/")
def root():
    return {"message": "Liteweb Agency API is running"}


# Health and database test endpoint
@app.get("/test")
def test_db():
    try:
        # Probe collections using pymongo
        collections = []
        if db is not None:
            collections = db.list_collection_names()
        return {
            "backend": "ok",
            "database": "configured" if db is not None else "not-configured",
            "database_url": "set" if database_url else "missing",
            "database_name": database_name or "missing",
            "connection_status": "connected" if db is not None else "not connected",
            "collections": collections,
        }
    except Exception as e:
        return {"backend": "ok", "database": f"error: {str(e)}"}


# Contact inquiry model and endpoint
class Inquiry(BaseModel):
    name: str = Field(..., min_length=2)
    email: EmailStr
    company: Optional[str] = None
    service: str = Field(..., description="Requested service")
    message: str = Field(..., min_length=5)


@app.post("/inquiries")
def create_inquiry(inquiry: Inquiry):
    try:
        doc_id = create_document("inquiry", inquiry)
        return {"status": "received", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Simple catalog of services (static for now)
@app.get("/services")
def list_services():
    return [
        {
            "id": "web-design",
            "title": "Web Design",
            "description": "Modern, responsive websites tailored to your brand.",
            "features": ["UX/UI", "Responsive", "SEO-ready", "Accessibility"],
        },
        {
            "id": "hosting",
            "title": "Managed Hosting",
            "description": "Fast, secure, and monitored cloud hosting.",
            "features": ["SSL", "Backups", "Monitoring", "CDN"],
        },
        {
            "id": "maintenance",
            "title": "Maintenance",
            "description": "Ongoing updates, security patches, and enhancements.",
            "features": ["Updates", "Security", "Performance", "Support"],
        },
    ]


# Expose schemas for DB viewer if needed
@app.get("/schema")
def get_schema():
    try:
        schemas_module = importlib.import_module("schemas")
        schema_dict = {}
        for name in dir(schemas_module):
            attr = getattr(schemas_module, name)
            if isinstance(attr, type) and issubclass(attr, BaseModel) and attr is not BaseModel:
                schema_dict[name] = attr.model_json_schema()
        return schema_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
