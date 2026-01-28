import asyncio
from datetime import datetime
from typing import Optional
from sqlalchemy import select, update, func
from src.models.tables import Dependency
from src.databases import db


class DependencyService:
    """Dependency management service"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

    async def _update_dependency_status(
        self,
        dependency_id: int,
        status: str,
        error_message: Optional[str] = None,
        installed_at: Optional[datetime] = None,
    ):
        """Update dependency status in database"""
        async for session in db.get_session():
            values = {"status": status}
            if error_message is not None:
                values["error_message"] = error_message
            if installed_at:
                values["installed_at"] = installed_at
            if status == "installed":
                values["error_message"] = None

            await session.execute(
                update(Dependency)
                .where(Dependency.id == dependency_id)
                .values(**values)
            )
            await session.commit()

    async def _get_or_create_dependency(
        self, dependency_type: str, package_name: str, version: Optional[str]
    ) -> int:
        """Get existing dependency or create new one, returns dependency_id"""
        async for session in db.get_session():
            result = await session.execute(
                select(Dependency).where(
                    Dependency.dependency_type == dependency_type,
                    Dependency.package_name == package_name,
                )
            )
            existing_dep = result.scalar_one_or_none()

            if existing_dep:
                await self._update_dependency_status(existing_dep.id, "installing")
                return existing_dep.id
            else:
                new_dep = Dependency(
                    dependency_type=dependency_type,
                    package_name=package_name,
                    version=version,
                    status="installing",
                )
                session.add(new_dep)
                await session.commit()
                await session.refresh(new_dep)
                return new_dep.id

    def _build_install_command(
        self, dependency_type: str, package_name: str, version: Optional[str]
    ) -> list:
        """Build installation command based on dependency type"""
        package_str = f"{package_name}=={version}" if version else package_name

        if dependency_type == "python":
            return ["uv", "pip", "install", "--system", package_str]
        else:  # node
            return ["pnpm", "add", "-g", package_str]

    def _build_result(
        self,
        success: bool,
        dependency_id: int,
        dependency_type: str,
        package_name: str,
        version: Optional[str],
        status: str,
        output: Optional[str],
        error: Optional[str],
        exit_code: Optional[int],
        started_at: datetime,
        finished_at: datetime,
    ) -> dict:
        """Build standardized result dictionary"""
        return {
            "success": success,
            "dependency_id": dependency_id,
            "dependency_type": dependency_type,
            "package_name": package_name,
            "version": version,
            "status": status,
            "output": output,
            "error": error,
            "exit_code": exit_code,
            "duration": (finished_at - started_at).total_seconds(),
            "started_at": started_at,
            "finished_at": finished_at,
        }

    async def install_dependency(
        self,
        dependency_type: str,
        package_name: str,
        version: Optional[str] = None,
        timeout: int = 300,
    ) -> dict:
        """Install a single dependency"""
        if dependency_type not in ["python", "node"]:
            return {
                "success": False,
                "error": f"Unsupported dependency type: {dependency_type}",
                "status": "failed",
            }

        started_at = datetime.now()

        try:
            # Get or create dependency record
            dependency_id = await self._get_or_create_dependency(
                dependency_type, package_name, version
            )

            # Build and execute installation command
            command = self._build_install_command(
                dependency_type, package_name, version
            )
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                finished_at = datetime.now()

                output = stdout.decode("utf-8") if stdout else None
                error = stderr.decode("utf-8") if stderr else None
                success = process.returncode == 0

                # Update database status
                await self._update_dependency_status(
                    dependency_id,
                    "installed" if success else "failed",
                    error if not success else None,
                    finished_at if success else None,
                )

                return self._build_result(
                    success,
                    dependency_id,
                    dependency_type,
                    package_name,
                    version,
                    "success" if success else "failed",
                    output,
                    error,
                    process.returncode,
                    started_at,
                    finished_at,
                )

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                finished_at = datetime.now()

                error_msg = f"Installation timed out after {timeout} seconds"
                await self._update_dependency_status(dependency_id, "failed", error_msg)

                return self._build_result(
                    False,
                    dependency_id,
                    dependency_type,
                    package_name,
                    version,
                    "timeout",
                    None,
                    error_msg,
                    None,
                    started_at,
                    finished_at,
                )

        except Exception as e:
            finished_at = datetime.now()

            if "dependency_id" in locals():
                await self._update_dependency_status(dependency_id, "failed", str(e))

            return self._build_result(
                False,
                locals().get("dependency_id", 0),
                dependency_type,
                package_name,
                version,
                "error",
                None,
                str(e),
                None,
                started_at,
                finished_at,
            )

    async def list_dependencies(
        self,
        dependency_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """List dependencies with pagination"""
        async for session in db.get_session():
            query = select(Dependency)

            if dependency_type:
                query = query.where(Dependency.dependency_type == dependency_type)
            if status:
                query = query.where(Dependency.status == status)

            # Get total count
            count_result = await session.execute(
                select(func.count()).select_from(query.subquery())
            )
            total = count_result.scalar()

            # Calculate pagination
            offset = (page - 1) * page_size
            total_pages = (total + page_size - 1) // page_size

            # Query paginated data
            result = await session.execute(
                query.order_by(Dependency.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            dependencies = result.scalars().all()

            items = [
                {
                    "id": dep.id,
                    "dependency_type": dep.dependency_type,
                    "package_name": dep.package_name,
                    "version": dep.version,
                    "status": dep.status,
                    "installed_at": dep.installed_at,
                    "error_message": dep.error_message,
                    "created_at": dep.created_at,
                    "updated_at": dep.updated_at,
                }
                for dep in dependencies
            ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }


# Singleton instance
dependency_service = DependencyService()
