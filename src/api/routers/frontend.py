"""
Frontend router for serving Jinja2 templates.
"""

from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Setup templates directory
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["Frontend"])


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "active_page": "home"}
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request, "active_page": "login"}
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page."""
    return templates.TemplateResponse(
        "auth/register.html",
        {"request": request, "active_page": "register"}
    )


@router.get("/listings", response_class=HTMLResponse)
async def listings_page(request: Request):
    """Browse listings page."""
    return templates.TemplateResponse(
        "listings/list.html",
        {"request": request, "active_page": "listings"}
    )


@router.get("/listings/new", response_class=HTMLResponse)
async def create_listing_page(request: Request):
    """Create new listing page."""
    return templates.TemplateResponse(
        "listings/form.html",
        {"request": request, "active_page": "listings", "listing_id": None}
    )


@router.get("/listings/{listing_id}", response_class=HTMLResponse)
async def listing_detail_page(request: Request, listing_id: int):
    """Listing detail page."""
    return templates.TemplateResponse(
        "listings/detail.html",
        {"request": request, "active_page": "listings", "listing_id": listing_id}
    )


@router.get("/listings/{listing_id}/edit", response_class=HTMLResponse)
async def edit_listing_page(request: Request, listing_id: int):
    """Edit listing page."""
    return templates.TemplateResponse(
        "listings/form.html",
        {"request": request, "active_page": "listings", "listing_id": listing_id}
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """User profile page."""
    return templates.TemplateResponse(
        "users/profile.html",
        {"request": request, "active_page": "profile"}
    )


@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """Users list page."""
    return templates.TemplateResponse(
        "users/list.html",
        {"request": request, "active_page": "users"}
    )
