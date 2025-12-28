"""
Listing CRUD router with filtering and sorting.
"""

from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc

from ...core.database import get_db
from ...models.models import Listing, User
from ...schemas.schemas import ListingCreate, ListingUpdate, ListingResponse, ListingList, Message
from ...services.auth import get_current_user
from ...core.exceptions import NotFoundError, ForbiddenError
from ...services.cache import get_cache, set_cache, invalidate_cache

router = APIRouter(prefix="/v1/listings", tags=["Listings"])


@router.post(
    "",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new listing"
)
async def create_listing(
    listing_data: ListingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new product listing.
    
    Requires authentication. The listing will be owned by the authenticated user.
    """
    listing = Listing(
        **listing_data.model_dump(),
        seller_id=current_user.id
    )
    
    db.add(listing)
    db.commit()
    db.refresh(listing)
    
    # Invalidate listings cache on create
    invalidate_cache("listing:*")
    
    return listing


@router.get(
    "",
    response_model=ListingList,
    summary="List all listings"
)
async def list_listings(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    seller_id: Optional[int] = Query(None, description="Filter by seller ID"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    sort_by: Literal["price", "created_at", "title"] = Query("created_at", description="Sort field"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of listings with filtering and sorting.
    
    This is a public endpoint - no authentication required for browsing.
    """
    query = db.query(Listing)
    
    # Apply filters
    if is_active is not None:
        query = query.filter(Listing.is_active == is_active)
    
    if category:
        query = query.filter(Listing.category == category)
    
    if seller_id:
        query = query.filter(Listing.seller_id == seller_id)
    
    if min_price is not None:
        query = query.filter(Listing.price >= min_price)
    
    if max_price is not None:
        query = query.filter(Listing.price <= max_price)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Listing, sort_by)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))
    
    # Apply pagination
    listings = query.offset(skip).limit(limit).all()
    
    return ListingList(
        items=listings,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/{listing_id}",
    response_model=ListingResponse,
    summary="Get listing by ID"
)
async def get_listing(
    listing_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific listing by ID. Public endpoint. Results are cached."""
    # Check cache first
    cache_key = f"listing:{listing_id}"
    cached = get_cache(cache_key)
    if cached:
        return cached
    
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise NotFoundError("Listing", listing_id)
    
    # Cache the result
    set_cache(cache_key, ListingResponse.model_validate(listing).model_dump(mode='json'), ttl_seconds=60)
    
    return listing


@router.put(
    "/{listing_id}",
    response_model=ListingResponse,
    summary="Update listing"
)
async def update_listing(
    listing_id: int,
    listing_data: ListingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a listing.
    
    Only the listing owner or admin can update.
    """
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise NotFoundError("Listing", listing_id)
    
    # Check authorization
    if listing.seller_id != current_user.id and current_user.role != "admin":
        raise ForbiddenError("You can only update your own listings")
    
    # Update fields
    update_data = listing_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(listing, field, value)
    
    db.commit()
    db.refresh(listing)
    
    # Invalidate cache on update
    invalidate_cache(f"listing:{listing_id}")
    
    return listing


@router.delete(
    "/{listing_id}",
    response_model=Message,
    summary="Delete listing"
)
async def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a listing.
    
    Only the listing owner or admin can delete.
    """
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise NotFoundError("Listing", listing_id)
    
    # Check authorization
    if listing.seller_id != current_user.id and current_user.role != "admin":
        raise ForbiddenError("You can only delete your own listings")
    
    db.delete(listing)
    db.commit()
    
    # Invalidate cache on delete
    invalidate_cache(f"listing:{listing_id}")
    
    return Message(message="Listing deleted successfully")
