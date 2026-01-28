from .auth import router as auth_router
from .tasks import router as tasks_router
from .settings import router as settings_router
from .executions import router as executions_router
from .scripts import router as scripts_router
from .stats import router as stats_router
from .dependencies import router as dependencies_router

__all__ = [
    "auth_router",
    "tasks_router",
    "settings_router",
    "executions_router",
    "scripts_router",
    "stats_router",
    "dependencies_router",
]
