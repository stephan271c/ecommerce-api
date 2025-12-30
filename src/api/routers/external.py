"""
External API router demonstrating async HTTP calls.
"""

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends
from ...services.rate_limit import RateLimiter
from ...services.auth import get_current_user
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/v1/external", tags=["External"])


class ExternalAPIResponse(BaseModel):
    """Response from external API call."""
    source: str
    data: dict
    message: Optional[str] = None


class BackgroundTaskStatus(BaseModel):
    """Status of background task."""
    message: str
    task_id: str


async def fetch_random_user() -> dict:
    """Async function to fetch a random user from public API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://randomuser.me/api/",
            timeout=10.0
        )
        return response.json()


def process_in_background(task_id: str, data: str):
    """
    Example background task.
    
    In production, this could be sending emails, processing files, etc.
    """
    import time
    import logging
    
    logger = logging.getLogger("background_task")
    logger.info(f"Starting background task {task_id}")
    
    # Simulate work
    time.sleep(2)
    
    logger.info(f"Completed background task {task_id}: processed '{data}'")


@router.get(
    "/random-user",
    response_model=ExternalAPIResponse,
    summary="Fetch random user from external API",
    dependencies=[Depends(get_current_user), Depends(RateLimiter(requests=5, window=60))]
)
async def get_random_user():
    """
    Demonstrates async HTTP call using httpx.
    
    Fetches a random user from randomuser.me API.
    """
    try:
        result = await fetch_random_user()
        return ExternalAPIResponse(
            source="randomuser.me",
            data=result
        )
    except httpx.HTTPError as e:
        return ExternalAPIResponse(
            source="randomuser.me",
            data={},
            message=f"Error fetching data: {str(e)}"
        )


@router.post(
    "/background-task",
    response_model=BackgroundTaskStatus,
    summary="Start a background task"
)
async def start_background_task(
    data: str,
    background_tasks: BackgroundTasks
):
    """
    Demonstrates FastAPI background tasks.
    
    Starts a task that processes data in the background
    while immediately returning a response.
    """
    import uuid
    task_id = str(uuid.uuid4())
    
    background_tasks.add_task(process_in_background, task_id, data)
    
    return BackgroundTaskStatus(
        message="Task started successfully",
        task_id=task_id
    )
