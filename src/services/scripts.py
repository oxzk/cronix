from pathlib import Path
from typing import List, Optional, Tuple
import asyncio
from datetime import datetime


class ScriptService:
    """Script management service"""

    _instance = None
    _script_dir = Path(__FILE__).parent.parent.parent / "data/scripts"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.script_dir = self._script_dir
        self.script_dir.mkdir(parents=True, exist_ok=True)
        self._initialized = True

    @staticmethod
    def get_script_type(filename: str) -> str:
        """Determine script type from file extension"""
        ext = Path(filename).suffix.lower()
        type_map = {
            ".py": "python",
            ".js": "javascript",
            ".sh": "shell",
            ".bash": "shell",
            ".zsh": "shell",
        }
        return type_map.get(ext, "unknown")

    @staticmethod
    def get_interpreter(script_type: str) -> Optional[List[str]]:
        """Get interpreter command for script type"""
        interpreters = {
            "python": ["uv", "run"],
            "javascript": ["node"],
            "shell": ["bash"],
        }
        return interpreters.get(script_type)

    def validate_path(
        self, script_path: str
    ) -> Tuple[bool, Optional[str], Optional[Path]]:
        """
        Validate script path for security
        Returns: (is_valid, error_message, full_path)
        """
        full_path = self.script_dir / script_path

        if not full_path.exists():
            return False, f"Script '{script_path}' not found", None

        # Verify the path is within script_dir for security
        try:
            full_path.resolve().relative_to(self.script_dir.resolve())
        except ValueError:
            return False, "Access denied: path outside script directory", None

        return True, None, full_path

    def build_tree(self, directory: Path, base_path: Path) -> List[dict]:
        """Build tree structure for scripts directory"""
        nodes = []

        try:
            items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        except PermissionError:
            return nodes

        for item in items:
            relative_path = str(item.relative_to(base_path))

            if item.is_dir():
                # Recursively build tree for subdirectories
                children = self.build_tree(item, base_path)
                nodes.append(
                    {
                        "name": item.name,
                        "type": "directory",
                        "path": relative_path,
                        "children": children if children else [],
                    }
                )
            elif item.is_file():
                script_type = self.get_script_type(item.name)
                if script_type != "unknown":
                    nodes.append(
                        {
                            "name": item.name,
                            "type": "file",
                            "path": relative_path,
                            "script_type": script_type,
                            "children": None,
                        }
                    )

        return nodes

    def list_scripts(self) -> List[dict]:
        """List all scripts in tree structure"""
        return self.build_tree(self.script_dir, self.script_dir)

    def get_script(
        self, script_path: str
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Get a specific script by path
        Returns: (success, error_message, script_data)
        """
        is_valid, error_msg, full_path = self.validate_path(script_path)
        if not is_valid:
            return False, error_msg, None

        if not full_path.is_file():
            return False, f"'{script_path}' is not a file", None

        try:
            script_type = self.get_script_type(full_path.name)
            content = full_path.read_text(encoding="utf-8")

            return (
                True,
                None,
                {
                    "name": script_path,
                    "type": script_type,
                    "content": content,
                    "path": str(full_path.resolve().relative_to(Path.cwd().resolve())),
                },
            )
        except Exception as e:
            return False, str(e), None

    def create_script(
        self, name: str, content: str
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Create a new script
        Returns: (success, error_message, script_data)
        """
        # Normalize path
        filename = name.replace("\\", "/")
        script_path = self.script_dir / filename

        if script_path.exists():
            return False, f"Script '{filename}' already exists", None

        # Validate file extension
        script_type = self.get_script_type(filename)
        if script_type == "unknown":
            return False, "Unsupported file type. Supported: .py, .js, .sh", None

        try:
            # Create parent directories if they don't exist
            script_path.parent.mkdir(parents=True, exist_ok=True)
            script_path.write_text(content, encoding="utf-8")

            return (
                True,
                None,
                {
                    "name": filename,
                    "type": script_type,
                    "content": content,
                    "path": str(
                        script_path.resolve().relative_to(Path.cwd().resolve())
                    ),
                },
            )
        except Exception as e:
            return False, f"Failed to create script: {str(e)}", None

    def update_script(
        self, script_path: str, new_name: str, content: str
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        Update an existing script
        Returns: (success, error_message, script_data)
        """
        is_valid, error_msg, old_path = self.validate_path(script_path)
        if not is_valid:
            return False, error_msg, None

        # Check if renaming/moving
        new_filename = new_name.replace("\\", "/")
        new_path = self.script_dir / new_filename

        # Validate file extension
        script_type = self.get_script_type(new_filename)
        if script_type == "unknown":
            return False, "Unsupported file type. Supported: .py, .js, .sh", None

        try:
            if new_filename != script_path:
                # Verify the new path is within script_dir for security
                try:
                    new_path.resolve().relative_to(self.script_dir.resolve())
                except ValueError:
                    return (
                        False,
                        "Access denied: path outside script directory",
                        None,
                    )

                if new_path.exists():
                    return False, f"Script '{new_filename}' already exists", None

                # Create parent directories if needed
                new_path.parent.mkdir(parents=True, exist_ok=True)
                old_path.rename(new_path)
                old_path = new_path

            old_path.write_text(content, encoding="utf-8")

            return (
                True,
                None,
                {
                    "name": new_filename,
                    "type": script_type,
                    "content": content,
                    "path": str(old_path.resolve().relative_to(Path.cwd().resolve())),
                },
            )
        except Exception as e:
            return False, f"Failed to update script: {str(e)}", None

    def delete_script(self, script_path: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a script
        Returns: (success, error_message)
        """
        is_valid, error_msg, full_path = self.validate_path(script_path)
        if not is_valid:
            return False, error_msg

        if not full_path.is_file():
            return False, f"'{script_path}' is not a file"

        try:
            # Delete the file
            full_path.unlink()

            # Remove empty parent directories
            parent = full_path.parent
            while parent != self.script_dir and parent.exists():
                try:
                    # Only remove if directory is empty
                    if not any(parent.iterdir()):
                        parent.rmdir()
                        parent = parent.parent
                    else:
                        break
                except (OSError, PermissionError):
                    break

            return True, None
        except Exception as e:
            return False, f"Failed to delete script: {str(e)}"

    async def run_script(
        self, script_path: str, args: Optional[List[str]] = None, timeout: int = 300
    ) -> dict:
        """
        Run a script with optional arguments
        Returns: execution result dict
        """
        is_valid, error_msg, full_path = self.validate_path(script_path)
        if not is_valid:
            return {
                "success": False,
                "error": error_msg,
                "script_path": script_path,
                "status": "error",
            }

        if not full_path.is_file():
            return {
                "success": False,
                "error": f"'{script_path}' is not a file",
                "script_path": script_path,
                "status": "error",
            }

        # Determine script type and interpreter
        script_type = self.get_script_type(full_path.name)
        if script_type == "unknown":
            return {
                "success": False,
                "error": "Cannot execute script with unknown type",
                "script_path": script_path,
                "status": "error",
            }

        interpreter = self.get_interpreter(script_type)
        if not interpreter:
            return {
                "success": False,
                "error": f"No interpreter found for script type: {script_type}",
                "script_path": script_path,
                "status": "error",
            }

        # Build command
        command = interpreter + [str(full_path)] + (args or [])

        started_at = datetime.now()
        try:
            # Run script with timeout
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.script_dir),
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
                finished_at = datetime.now()
                duration = (finished_at - started_at).total_seconds()

                output = stdout.decode("utf-8") if stdout else None
                error = stderr.decode("utf-8") if stderr else None

                status = "success" if process.returncode == 0 else "failed"

                return {
                    "success": True,
                    "script_path": script_path,
                    "status": status,
                    "output": output,
                    "error": error,
                    "exit_code": process.returncode,
                    "duration": duration,
                    "started_at": started_at,
                    "finished_at": finished_at,
                }

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                finished_at = datetime.now()
                duration = (finished_at - started_at).total_seconds()

                return {
                    "success": False,
                    "script_path": script_path,
                    "status": "timeout",
                    "output": None,
                    "error": f"Execution timed out after {timeout} seconds",
                    "exit_code": None,
                    "duration": duration,
                    "started_at": started_at,
                    "finished_at": finished_at,
                }

        except Exception as e:
            finished_at = datetime.now()
            duration = (finished_at - started_at).total_seconds()

            return {
                "success": False,
                "script_path": script_path,
                "status": "error",
                "output": None,
                "error": str(e),
                "exit_code": None,
                "duration": duration,
                "started_at": started_at,
                "finished_at": finished_at,
            }

    def get_stats(self) -> dict:
        """Get statistics about all scripts"""
        total_scripts = 0
        by_type = {}
        total_size = 0

        def scan_directory(directory: Path):
            nonlocal total_scripts, total_size

            for item in directory.iterdir():
                if item.is_dir():
                    scan_directory(item)
                elif item.is_file():
                    script_type = self.get_script_type(item.name)
                    if script_type != "unknown":
                        total_scripts += 1
                        total_size += item.stat().st_size
                        by_type[script_type] = by_type.get(script_type, 0) + 1

        try:
            if self.script_dir.exists():
                scan_directory(self.script_dir)

            return {
                "total_scripts": total_scripts,
                "by_type": by_type,
                "total_size_bytes": total_size,
            }
        except Exception as e:
            raise Exception(f"Failed to get stats: {str(e)}")


# Singleton instance
script_service = ScriptService()
