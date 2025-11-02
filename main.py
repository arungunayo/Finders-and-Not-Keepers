import requests
from pydantic import Field, HttpUrl, BaseModel
from typing import Optional, Literal, List
from datetime import datetime
import psycopg2
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os
from fastapi import (
    FastAPI, UploadFile, File, Form, Depends,
    Query, HTTPException, Request
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from huggingface_hub import InferenceClient
import json

# -------------------------------------------------------------
#  Basic setup
# -------------------------------------------------------------
app = FastAPI()

# Setup Jinja2 templates (absolute path)
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# -------------------------------------------------------------
#  Layer 1: Data Schemas (Pydantic)
# -------------------------------------------------------------
class ItemCreate(BaseModel):
    item_type: Literal["lost", "found"] = Field(description="Whether the item was lost or found")
    item_name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    location: str = Field(min_length=2)
    contact_info: str = Field(description="Email or phone of the reporter")
    image_url: Optional[HttpUrl] = Field(None, description="Link to image hosted on Cloudinary")
    tag: Optional[str] = Field(None, description="Auto-generated category tag")

    @classmethod
    def as_form(
        cls,
        item_type: str = Form(...),
        item_name: str = Form(...),
        description: Optional[str] = Form(None),
        location: str = Form(...),
        contact_info: str = Form(...),
    ):
        return cls(
            item_type=item_type,
            item_name=item_name,
            description=description,
            location=location,
            contact_info=contact_info,
        )


class ItemResponse(ItemCreate):
    id: int
    created_at: datetime


class ItemsListResponse(BaseModel):
    items: List[ItemResponse]


# -------------------------------------------------------------
#  Layer 2: Database setup (PostgreSQL / Neon)
# -------------------------------------------------------------
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            item_type VARCHAR(20) NOT NULL,
            item_name VARCHAR(100) NOT NULL,
            description TEXT,
            location VARCHAR(255) NOT NULL,
            contact_info VARCHAR(100) NOT NULL,
            image_path TEXT,
            tag VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

# Initialize database at startup
init_db()


# -------------------------------------------------------------
#  Layer 3: Cloudinary setup
# -------------------------------------------------------------
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)


def save_uploaded_image(file: UploadFile) -> str:
    if file.filename:
        upload_result = cloudinary.uploader.upload(file.file, folder="lost_and_found/")
        return upload_result.get("secure_url", "")
    return ""


# -------------------------------------------------------------
#  Layer 4: Utility functions
# -------------------------------------------------------------

client = InferenceClient(api_key=os.getenv("HUGGINGFACE_API_KEY"))
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
HEADERS = {"Authorization": f"Bearer {client}"}

def auto_tag_item(item_name: str, description: str) -> str:
    """Use Hugging Face zero-shot classifier for tagging."""
    text = f"{item_name} {description}"
    labels = [
        # Core everyday objects
        "electronics", "clothing", "accessories", "documents", "books",
        "sports_equipment", "toys", "keys", "tools",

        # Personal items
        "wallets_and_purses", "bags_and_backpacks", "jewelry", "watches",
        "glasses_and_sunglasses", "umbrellas", "cosmetics_and_makeup",

        # Identification / official items
        "id_cards_and_badges", "credit_cards", "driver_license", "passport", "tickets",

        # Academic / work items
        "stationery", "notebooks", "laptops_and_tablets", "usb_drives",
        "calculators", "school_supplies", "office_supplies",

        # Transport / mobility
        "bicycles", "helmets", "vehicle_keys",

        # Miscellaneous
        "food_containers", "bottles", "miscellaneous"
    ]
    payload = {
        "inputs": text,
        "parameters": {
            "candidate_labels": labels,
            "multi_label": False
        }
    }

    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload)
        result = response.json()
        if isinstance(result, dict) and "labels" in result:
            return result["labels"][0].lower()
        elif isinstance(result, list) and "label" in result[0]:
            return result[0]["label"].lower()
        else:
            print("Unexpected response:", result)
            return "miscellaneous"
    except Exception as e:
        print("Tagging error:", e)
        return "miscellaneous"


# -------------------------------------------------------------
#  Layer 5: Template routes
# -------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/report-lost", response_class=HTMLResponse)
async def report_lost(request: Request):
    return templates.TemplateResponse("report_form.html", {
        "request": request,
        "item_type": "lost",
        "title": "Report Lost Item"
    })


@app.get("/report-found", response_class=HTMLResponse)
async def report_found(request: Request):
    return templates.TemplateResponse("report_form.html", {
        "request": request,
        "item_type": "found",
        "title": "Report Found Item"
    })


@app.get("/view-items", response_class=HTMLResponse)
async def view_items(request: Request, search: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    if search:
        cursor.execute("""
            SELECT * FROM items
            WHERE item_name ILIKE %s OR location ILIKE %s
            ORDER BY created_at DESC
        """, (f"%{search}%", f"%{search}%"))
    else:
        cursor.execute("SELECT * FROM items ORDER BY created_at DESC")

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    items = [dict(zip(columns, row)) for row in rows]
    conn.close()

    return templates.TemplateResponse("items.html", {
        "request": request,
        "items": items,
        "search": search
    })


@app.get("/item/{item_id}", response_class=HTMLResponse)
async def view_item_detail(request: Request, item_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = %s", (item_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Item not found")

    columns = ["id", "item_type", "item_name", "description", "location", "contact_info",
               "image_path", "tag", "created_at"]
    item = dict(zip(columns, row))
    return templates.TemplateResponse("item_detail.html", {"request": request, "item": item})


# -------------------------------------------------------------
#  Layer 6: Form submission
# -------------------------------------------------------------
@app.post("/submit-item")
async def submit_item(
    item: ItemCreate = Depends(ItemCreate.as_form),
    image: UploadFile = File(None)
):
    image_url = ""
    if image and image.filename:
        image_url = save_uploaded_image(image)
        item.image_url = image_url

    tag = auto_tag_item(item.item_name, item.description or "")
    item.tag = tag

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO items (item_type, item_name, description, location, contact_info, image_path, tag)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (item.item_type, item.item_name, item.description, item.location,
          item.contact_info, item.image_url, item.tag))
    conn.commit()
    conn.close()

    return RedirectResponse(url="/view-items", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
