# app/routers/user.py
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.crud.user import list_users, get_user, create_user, update_user, delete_user
from app.core.database import get_db
from typing import List
from app.models import User as UserModel
from app.core.database import get_db
from app import crud, schemas

logger = logging.getLogger("routers.user")
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserRead])
async def route_list_users(db: AsyncSession = Depends(get_db)):
    logger.info("GET /users")
    users = await list_users(db)
    return users

@router.get("/{user_id}", response_model=UserRead)
async def route_get_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserRead, status_code=201)
async def route_create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    obj = await create_user(db, payload)
    return obj

@router.put("/{user_id}", response_model=UserRead)
async def route_update_user(user_id: UUID, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    updated = await update_user(db, user, payload)
    return updated

@router.delete("/{user_id}", response_model=UserRead)
async def route_delete_user(user_id: UUID, db: AsyncSession = Depends(get_db)):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    deleted = await delete_user(db, user)
    return deleted

@router.patch("/{user_id}/city", response_model=UserRead)
async def update_city(
    user_id: UUID,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.city is None:
        raise HTTPException(status_code=400, detail="City is required")

    user.city = data.city
    await db.commit()
    await db.refresh(user)

    return user

# === SESSIONS ===
@router.post("/{user_id}/sessions", response_model=schemas.Session)
async def create_session(user_id: str, sess_in: schemas.SessionCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Creating session for user={user_id}")
    sess_in.user_id = user_id
    return await crud.session.create(db, sess_in)


# === DEVICE TOKENS ===
@router.post("/{user_id}/tokens", response_model=schemas.DeviceToken)
async def register_device_token(user_id: str, token_in: schemas.DeviceTokenCreate, db: AsyncSession = Depends(get_db)):
    token_in.user_id = user_id
    logger.info(f"Registering device token for user={user_id}")
    return await crud.device_token.create(db, token_in)


# === FAVORITES ===
@router.post("/{user_id}/favorites", response_model=schemas.UserFavorite)
async def add_favorite(user_id: str, fav_in: schemas.UserFavoriteCreate, db: AsyncSession = Depends(get_db)):
    fav_in.user_id = user_id
    logger.info(f"Adding favorite shop={fav_in.shop_id} for user={user_id}")
    return await crud.user_favorite.create(db, fav_in)


@router.get("/{user_id}/favorites", response_model=List[schemas.UserFavorite])
async def list_favorites(user_id: str, db: AsyncSession = Depends(get_db)):
    logger.info(f"Listing favorites for user={user_id}")
    result = await crud.user_favorite.get_multi(db)
    return [f for f in result if str(f.user_id) == user_id]