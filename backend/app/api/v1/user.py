
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ...cruds import user_crud
from ...schemas import schemas
from ...db import database, models
from ...core.security import get_current_user

router = APIRouter()

@router.get("/", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve users. This is used to select users for a new conversation.
    """
    users = user_crud.get_users(db, skip=skip, limit=limit)
    # Filter out the current user from the list
    return [user for user in users if user.id != current_user.id]