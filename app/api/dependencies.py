"""FastAPI 依赖。"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.application.container import ApplicationContainer
from app.infrastructure.auth.jwt import Principal


def get_container(request: Request) -> ApplicationContainer:
    return request.app.state.container


Container = Annotated[ApplicationContainer, Depends(get_container)]


def get_current_user(request: Request) -> Principal:
    return request.state.user


CurrentUser = Annotated[Principal, Depends(get_current_user)]
