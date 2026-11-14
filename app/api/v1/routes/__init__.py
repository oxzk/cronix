"""路由聚合。"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import (
    auth,
    backups,
    health,
    monitors,
    runs,
    scripts,
    stats,
    system_settings,
    tasks,
)

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(tasks.router)
router.include_router(runs.router)
router.include_router(monitors.router)
router.include_router(scripts.router)
router.include_router(backups.router)
router.include_router(stats.router)
router.include_router(system_settings.router)
