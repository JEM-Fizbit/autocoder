"""
Process Registry
================

Central registry for tracking all spawned processes including agents and their
child processes (MCP servers like Playwright).

Provides visibility into all running processes and emergency kill functionality.
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Literal, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Information about a tracked process."""
    pid: int
    name: str  # "agent", "playwright-mcp", "feature-mcp", "node", etc.
    project_name: str
    status: Literal["running", "paused", "stopped"] = "running"
    started_at: datetime = field(default_factory=datetime.now)
    parent_pid: Optional[int] = None
    cmdline: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "pid": self.pid,
            "name": self.name,
            "project_name": self.project_name,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "parent_pid": self.parent_pid,
            "cmdline": self.cmdline[:200] if self.cmdline else "",  # Truncate long cmdlines
        }


class ProcessRegistry:
    """
    Central registry for tracking all spawned processes.

    Thread-safe singleton that tracks:
    - Agent processes (main autonomous_agent_demo.py processes)
    - Child processes (MCP servers, browsers, etc.)
    """

    _instance: Optional["ProcessRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "ProcessRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._processes: Dict[int, ProcessInfo] = {}
        self._registry_lock = threading.Lock()
        self._initialized = True
        logger.info("Process registry initialized")

    def register(
        self,
        pid: int,
        name: str,
        project_name: str,
        parent_pid: Optional[int] = None,
        cmdline: str = "",
    ) -> ProcessInfo:
        """
        Register a process in the registry.

        Args:
            pid: Process ID
            name: Human-readable name (e.g., "agent", "playwright-mcp")
            project_name: Associated project name
            parent_pid: Parent process PID (for child processes)
            cmdline: Command line that started the process

        Returns:
            The registered ProcessInfo
        """
        with self._registry_lock:
            info = ProcessInfo(
                pid=pid,
                name=name,
                project_name=project_name,
                parent_pid=parent_pid,
                cmdline=cmdline,
            )
            self._processes[pid] = info
            logger.info(f"Registered process: {name} (PID {pid}) for project {project_name}")
            return info

    def unregister(self, pid: int) -> Optional[ProcessInfo]:
        """
        Remove a process from the registry.

        Args:
            pid: Process ID to unregister

        Returns:
            The removed ProcessInfo, or None if not found
        """
        with self._registry_lock:
            info = self._processes.pop(pid, None)
            if info:
                logger.info(f"Unregistered process: {info.name} (PID {pid})")
            return info

    def update_status(self, pid: int, status: Literal["running", "paused", "stopped"]) -> bool:
        """
        Update the status of a registered process.

        Args:
            pid: Process ID
            status: New status

        Returns:
            True if process was found and updated, False otherwise
        """
        with self._registry_lock:
            if pid in self._processes:
                self._processes[pid].status = status
                return True
            return False

    def get_all(self) -> List[ProcessInfo]:
        """Get all registered processes."""
        with self._registry_lock:
            return list(self._processes.values())

    def get_by_project(self, project_name: str) -> List[ProcessInfo]:
        """Get all processes for a specific project."""
        with self._registry_lock:
            return [p for p in self._processes.values() if p.project_name == project_name]

    def get_by_pid(self, pid: int) -> Optional[ProcessInfo]:
        """Get a process by PID."""
        with self._registry_lock:
            return self._processes.get(pid)

    def discover_children(self, parent_pid: int, project_name: str) -> List[ProcessInfo]:
        """
        Discover and register child processes of a parent process.

        Uses psutil to find all child processes recursively and registers
        them with appropriate names based on their command line.

        Args:
            parent_pid: PID of the parent process
            project_name: Project name to associate with children

        Returns:
            List of newly discovered and registered ProcessInfo objects
        """
        discovered = []

        try:
            parent = psutil.Process(parent_pid)
            children = parent.children(recursive=True)

            for child in children:
                if child.pid in self._processes:
                    continue  # Already registered

                try:
                    cmdline = " ".join(child.cmdline())
                    name = self._identify_process(cmdline, child.name())

                    info = self.register(
                        pid=child.pid,
                        name=name,
                        project_name=project_name,
                        parent_pid=parent_pid,
                        cmdline=cmdline,
                    )
                    discovered.append(info)

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.warning(f"Could not discover children of PID {parent_pid}: {e}")

        return discovered

    def _identify_process(self, cmdline: str, proc_name: str) -> str:
        """
        Identify a process type from its command line.

        Args:
            cmdline: Full command line
            proc_name: Process name from psutil

        Returns:
            Human-readable process name
        """
        cmdline_lower = cmdline.lower()

        # MCP servers
        if "playwright" in cmdline_lower or "@playwright/mcp" in cmdline_lower:
            return "playwright-mcp"
        if "feature_mcp" in cmdline_lower:
            return "feature-mcp"

        # Browsers (spawned by Playwright)
        if "chromium" in cmdline_lower or "chrome" in cmdline_lower:
            if "helper" in cmdline_lower:
                return "chrome-helper"
            return "chrome-browser"
        if "firefox" in cmdline_lower:
            return "firefox-browser"
        if "webkit" in cmdline_lower or "safari" in cmdline_lower:
            return "webkit-browser"

        # Node.js processes
        if "node" in proc_name.lower() or "npx" in cmdline_lower:
            if "vite" in cmdline_lower:
                return "vite-dev-server"
            if "next" in cmdline_lower:
                return "next-dev-server"
            return "node-process"

        # Python processes
        if "python" in proc_name.lower():
            return "python-subprocess"

        # Claude CLI
        if "claude" in cmdline_lower:
            return "claude-cli"

        return proc_name or "unknown"

    def kill_process(self, pid: int, force: bool = False) -> tuple[bool, str]:
        """
        Kill a specific process.

        Args:
            pid: Process ID to kill
            force: If True, use SIGKILL instead of SIGTERM

        Returns:
            Tuple of (success, message)
        """
        try:
            proc = psutil.Process(pid)

            if force:
                proc.kill()  # SIGKILL
            else:
                proc.terminate()  # SIGTERM

                # Wait briefly for graceful shutdown
                try:
                    proc.wait(timeout=3)
                except psutil.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=2)

            self.unregister(pid)
            return True, f"Process {pid} terminated"

        except psutil.NoSuchProcess:
            self.unregister(pid)
            return True, f"Process {pid} already terminated"
        except psutil.AccessDenied:
            return False, f"Access denied to kill process {pid}"
        except Exception as e:
            return False, f"Failed to kill process {pid}: {e}"

    def kill_by_project(self, project_name: str, force: bool = False) -> tuple[int, int]:
        """
        Kill all processes for a specific project.

        Args:
            project_name: Project name
            force: If True, use SIGKILL

        Returns:
            Tuple of (killed_count, failed_count)
        """
        processes = self.get_by_project(project_name)
        killed = 0
        failed = 0

        # Kill children first, then parents
        sorted_procs = sorted(processes, key=lambda p: p.parent_pid is None)

        for proc in sorted_procs:
            success, _ = self.kill_process(proc.pid, force)
            if success:
                killed += 1
            else:
                failed += 1

        return killed, failed

    def kill_all(self, force: bool = False) -> tuple[int, int]:
        """
        Kill all registered processes.

        Args:
            force: If True, use SIGKILL

        Returns:
            Tuple of (killed_count, failed_count)
        """
        processes = self.get_all()
        killed = 0
        failed = 0

        # Kill children first, then parents
        sorted_procs = sorted(processes, key=lambda p: p.parent_pid is None)

        for proc in sorted_procs:
            success, _ = self.kill_process(proc.pid, force)
            if success:
                killed += 1
            else:
                failed += 1

        return killed, failed

    def pause_process(self, pid: int) -> tuple[bool, str]:
        """
        Pause a specific process using SIGSTOP.

        Args:
            pid: Process ID to pause

        Returns:
            Tuple of (success, message)
        """
        try:
            proc = psutil.Process(pid)
            proc.suspend()
            self.update_status(pid, "paused")
            return True, f"Process {pid} paused"
        except psutil.NoSuchProcess:
            self.unregister(pid)
            return False, f"Process {pid} not found"
        except psutil.AccessDenied:
            return False, f"Access denied to pause process {pid}"
        except Exception as e:
            return False, f"Failed to pause process {pid}: {e}"

    def resume_process(self, pid: int) -> tuple[bool, str]:
        """
        Resume a paused process.

        Args:
            pid: Process ID to resume

        Returns:
            Tuple of (success, message)
        """
        try:
            proc = psutil.Process(pid)
            proc.resume()
            self.update_status(pid, "running")
            return True, f"Process {pid} resumed"
        except psutil.NoSuchProcess:
            self.unregister(pid)
            return False, f"Process {pid} not found"
        except psutil.AccessDenied:
            return False, f"Access denied to resume process {pid}"
        except Exception as e:
            return False, f"Failed to resume process {pid}: {e}"

    def cleanup_dead_processes(self) -> int:
        """
        Remove dead processes from the registry.

        Returns:
            Number of dead processes cleaned up
        """
        cleaned = 0
        with self._registry_lock:
            dead_pids = []
            for pid in self._processes:
                if not psutil.pid_exists(pid):
                    dead_pids.append(pid)

            for pid in dead_pids:
                del self._processes[pid]
                cleaned += 1

        if cleaned:
            logger.info(f"Cleaned up {cleaned} dead process(es) from registry")

        return cleaned

    def get_process_tree(self) -> List[dict]:
        """
        Get all processes organized as a tree structure.

        Returns:
            List of root processes with nested children
        """
        self.cleanup_dead_processes()

        processes = self.get_all()

        # Group by project
        by_project: Dict[str, List[ProcessInfo]] = {}
        for proc in processes:
            if proc.project_name not in by_project:
                by_project[proc.project_name] = []
            by_project[proc.project_name].append(proc)

        # Build tree for each project
        result = []
        for project_name, procs in by_project.items():
            # Find root processes (no parent or parent not in our list)
            pids = {p.pid for p in procs}
            roots = [p for p in procs if p.parent_pid is None or p.parent_pid not in pids]
            children_map: Dict[int, List[ProcessInfo]] = {}

            for proc in procs:
                if proc.parent_pid and proc.parent_pid in pids:
                    if proc.parent_pid not in children_map:
                        children_map[proc.parent_pid] = []
                    children_map[proc.parent_pid].append(proc)

            def build_node(proc: ProcessInfo) -> dict:
                node = proc.to_dict()
                node["children"] = [
                    build_node(child) for child in children_map.get(proc.pid, [])
                ]
                return node

            project_tree = {
                "project_name": project_name,
                "processes": [build_node(root) for root in roots],
                "total_count": len(procs),
            }
            result.append(project_tree)

        return result


# Module-level singleton accessor
def get_registry() -> ProcessRegistry:
    """Get the singleton ProcessRegistry instance."""
    return ProcessRegistry()
