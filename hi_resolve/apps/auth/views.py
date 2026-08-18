from __future__ import annotations

from typing import Annotated

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from hi_resolve.db import User, get_db, utcnow
from hi_resolve.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])

oauth = OAuth()
_oauth_registered = False


def configure_oauth() -> None:
    global _oauth_registered
    if _oauth_registered:
        return
    client_id = settings.google_client_id
    client_secret = settings.google_client_secret
    if not client_id or not client_secret:
        return
    oauth.register(
        name="google",
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    _oauth_registered = True


def google_configured() -> bool:
    return settings.google_configured


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


def require_user(
    user: Annotated[User | None, Depends(get_current_user)],
) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    return user


@router.get("/login")
async def login(request: Request):
    configure_oauth()
    if not google_configured() or not _oauth_registered:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth не настроен. Заполните GOOGLE_CLIENT_ID и GOOGLE_CLIENT_SECRET в .env",
        )
    redirect_uri = settings.oauth_redirect_uri or str(request.url_for("auth_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback", name="auth_callback")
async def auth_callback(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    configure_oauth()
    if not _oauth_registered:
        raise HTTPException(status_code=503, detail="Google OAuth не настроен")

    token = await oauth.google.authorize_access_token(request)
    info = token.get("userinfo")
    if not info:
        info = await oauth.google.userinfo(token=token)

    google_id = info.get("sub")
    email = info.get("email")
    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Не удалось получить профиль Google")

    user = db.query(User).filter(User.google_id == google_id).one_or_none()
    if user is None:
        user = User(
            google_id=google_id,
            email=email,
            name=info.get("name") or "",
            picture=info.get("picture") or "",
            created_at=utcnow(),
        )
        db.add(user)
    else:
        user.email = email
        user.name = info.get("name") or user.name
        user.picture = info.get("picture") or user.picture

    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=302)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me")
async def me(user: Annotated[User | None, Depends(get_current_user)]):
    if user is None:
        return {"authenticated": False, "user": None, "google_configured": google_configured()}
    return {
        "authenticated": True,
        "google_configured": google_configured(),
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
        },
    }
