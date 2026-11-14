"""ApplicationContainer: 组合根 — 创建/装配/关闭全部资源与服务。"""

from __future__ import annotations

from app.application.services.auth import AuthService
from app.application.services.backup import BackupService
from app.application.services.execution import ExecutionService
from app.application.services.logging import LoggingService
from app.application.services.monitor import MonitorService
from app.application.services.monitor_scheduler import MonitorSchedulerService
from app.application.services.notification import NotificationService
from app.application.services.scheduler import SchedulerService
from app.application.services.script import ScriptService
from app.application.services.stats import StatsService
from app.application.services.system_setting import SystemSettingService
from app.application.services.task import TaskService
from app.core.config import Settings
from app.infrastructure.auth.jwt import JWTCodec
from app.infrastructure.database.engine import Database
from app.runtime.event import EventBus
from app.runtime.execution.lifecycle import ExecutionLifecycle
from app.runtime.execution.logs import RunLogBuffer
from app.runtime.logger import RuntimeLogger
from app.runtime.state import RuntimeState


class ApplicationContainer:
    def __init__(
        self,
        settings: Settings,
        logging_service: LoggingService,
        database: Database,
        system_settings: SystemSettingService,
        auth: AuthService,
        events: EventBus,
        executions: ExecutionService,
        tasks: TaskService,
        scheduler: SchedulerService,
        notification: NotificationService,
        stats: StatsService,
        scripts: ScriptService,
        monitors: MonitorService,
        monitor_scheduler: MonitorSchedulerService,
        backups: BackupService,
        runtime_state: RuntimeState,
    ) -> None:
        self.settings = settings
        self.logging_service = logging_service
        self.database = database
        self.system_settings = system_settings
        self.auth = auth
        self.events = events
        self.executions = executions
        self.tasks = tasks
        self.scheduler = scheduler
        self.notification = notification
        self.stats = stats
        self.scripts = scripts
        self.monitors = monitors
        self.monitor_scheduler = monitor_scheduler
        self.backups = backups
        self.runtime_state = runtime_state

    @property
    def session_factory(self):  # type: ignore[no-untyped-def]
        return self.database.session_factory

    @classmethod
    async def create(cls, settings: Settings) -> "ApplicationContainer":
        logging_service = LoggingService(settings.logging)

        database = Database(settings.database)
        await database.initialize()
        session_factory = database.session_factory

        system_settings = SystemSettingService(session_factory, logging_service)
        await system_settings.bootstrap(settings)

        # 数据库日志配置覆盖 env(热更新起点)
        db_logging = await system_settings.load_logging(settings)
        logging_service.reload(db_logging.model_dump(mode="json"))

        # system/base 覆盖 runtime 配置(启动初值; 运行中 PUT 实时生效)
        settings = await system_settings.load_system(settings)
        runtime_state = RuntimeState(settings.runtime)
        system_settings.attach_runtime_state(runtime_state)

        async def reload_after_restore() -> None:
            """恢复备份后重新加载基础配置与日志配置。"""
            await system_settings.refresh_completeness()
            loaded = await system_settings.load_system(settings)
            runtime_state.apply(loaded.runtime.model_dump())
            log_cfg = await system_settings.load_logging(loaded)
            logging_service.reload(log_cfg.model_dump(mode="json"))

        auth = AuthService(session_factory, JWTCodec(settings.jwt))
        await auth.bootstrap()

        events = EventBus()
        run_logs = RunLogBuffer()
        executions = ExecutionService(session_factory, run_logs, runtime_state)
        runtime_logger = RuntimeLogger(run_logs)
        lifecycle = ExecutionLifecycle(
            events=events,
            run_logs=run_logs,
            runtime_logger=runtime_logger,
            runtime_state=runtime_state,
            on_running=executions.on_running,
            on_terminal=executions.on_terminal,
        )
        executions.attach_lifecycle(lifecycle)

        notification = NotificationService(session_factory, runtime_state)
        events.subscribe(notification.handle_event)

        tasks = TaskService(session_factory, executions)
        scheduler = SchedulerService(session_factory, executions, runtime_state)
        stats = StatsService(session_factory)
        scripts = ScriptService(session_factory)
        monitors = MonitorService(session_factory, events)
        monitor_scheduler = MonitorSchedulerService(session_factory, monitors, runtime_state)

        async def handle_before_restore() -> None:
            runtime_state.set_maintenance(True)
            await executions.cancel_all()

        async def handle_after_restore() -> None:
            try:
                await reload_after_restore()
            finally:
                runtime_state.set_maintenance(False)

        backups = BackupService(
            session_factory,
            runtime_state=runtime_state,
            before_restore=handle_before_restore,
            on_restored=handle_after_restore,
        )

        await executions.recover()
        await scheduler.start()
        await monitor_scheduler.start()

        return cls(
            settings=settings,
            logging_service=logging_service,
            database=database,
            system_settings=system_settings,
            auth=auth,
            events=events,
            executions=executions,
            tasks=tasks,
            scheduler=scheduler,
            notification=notification,
            stats=stats,
            scripts=scripts,
            monitors=monitors,
            monitor_scheduler=monitor_scheduler,
            backups=backups,
            runtime_state=runtime_state,
        )

    async def shutdown(self) -> None:
        await self.monitor_scheduler.stop()
        await self.monitors.close()
        await self.scheduler.stop()
        await self.executions.close()
        await self.database.close()
        self.logging_service.close()
