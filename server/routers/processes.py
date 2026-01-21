"""
Processes Router
================

API endpoints for viewing and managing all running processes across projects.
Provides visibility into agents, MCP servers, browsers, and other child processes.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.process_registry import get_registry


router = APIRouter(prefix="/api/processes", tags=["processes"])


# Response models
class ProcessInfo(BaseModel):
    """Information about a single process."""
    pid: int
    name: str
    project_name: str
    status: str
    started_at: str
    parent_pid: Optional[int] = None
    cmdline: str = ""
    children: List["ProcessInfo"] = []


class ProjectProcesses(BaseModel):
    """Processes grouped by project."""
    project_name: str
    processes: List[ProcessInfo]
    total_count: int


class ProcessActionResponse(BaseModel):
    """Response for process actions (kill/pause/resume)."""
    success: bool
    message: str


class KillAllResponse(BaseModel):
    """Response for kill-all action."""
    killed: int
    failed: int
    message: str


# Rebuild model for recursive type
ProcessInfo.model_rebuild()


@router.get("", response_model=List[ProjectProcesses])
async def list_all_processes():
    """
    Get all running processes grouped by project.

    Returns a tree structure showing agents and their child processes.
    """
    registry = get_registry()
    return registry.get_process_tree()


@router.get("/flat", response_model=List[ProcessInfo])
async def list_all_processes_flat():
    """
    Get all running processes as a flat list.

    Useful for simpler displays or filtering.
    """
    registry = get_registry()
    processes = registry.get_all()
    return [p.to_dict() for p in processes]


@router.get("/project/{project_name}", response_model=List[ProcessInfo])
async def list_project_processes(project_name: str):
    """Get all processes for a specific project."""
    registry = get_registry()
    processes = registry.get_by_project(project_name)
    return [p.to_dict() for p in processes]


@router.post("/{pid}/kill", response_model=ProcessActionResponse)
async def kill_process(pid: int, force: bool = False):
    """
    Kill a specific process.

    Args:
        pid: Process ID to kill
        force: If True, use SIGKILL instead of SIGTERM
    """
    registry = get_registry()

    # Verify process is in our registry
    process = registry.get_by_pid(pid)
    if not process:
        raise HTTPException(
            status_code=404,
            detail=f"Process {pid} not found in registry"
        )

    success, message = registry.kill_process(pid, force=force)
    return ProcessActionResponse(success=success, message=message)


@router.post("/project/{project_name}/kill", response_model=KillAllResponse)
async def kill_project_processes(project_name: str, force: bool = False):
    """
    Kill all processes for a specific project.

    Args:
        project_name: Project name
        force: If True, use SIGKILL
    """
    registry = get_registry()
    killed, failed = registry.kill_by_project(project_name, force=force)

    return KillAllResponse(
        killed=killed,
        failed=failed,
        message=f"Killed {killed} process(es), {failed} failed"
    )


@router.post("/kill-all", response_model=KillAllResponse)
async def kill_all_processes(force: bool = False):
    """
    Emergency stop - kill ALL registered processes.

    Args:
        force: If True, use SIGKILL for immediate termination
    """
    registry = get_registry()
    killed, failed = registry.kill_all(force=force)

    return KillAllResponse(
        killed=killed,
        failed=failed,
        message=f"Emergency stop complete. Killed {killed} process(es), {failed} failed"
    )


@router.post("/{pid}/pause", response_model=ProcessActionResponse)
async def pause_process(pid: int):
    """Pause a specific process using SIGSTOP."""
    registry = get_registry()

    process = registry.get_by_pid(pid)
    if not process:
        raise HTTPException(
            status_code=404,
            detail=f"Process {pid} not found in registry"
        )

    success, message = registry.pause_process(pid)
    return ProcessActionResponse(success=success, message=message)


@router.post("/{pid}/resume", response_model=ProcessActionResponse)
async def resume_process(pid: int):
    """Resume a paused process."""
    registry = get_registry()

    process = registry.get_by_pid(pid)
    if not process:
        raise HTTPException(
            status_code=404,
            detail=f"Process {pid} not found in registry"
        )

    success, message = registry.resume_process(pid)
    return ProcessActionResponse(success=success, message=message)


@router.get("/count")
async def get_process_count():
    """Get a count of running processes."""
    registry = get_registry()
    processes = registry.get_all()

    # Count by type
    agents = sum(1 for p in processes if p.name == "agent")
    browsers = sum(1 for p in processes if "browser" in p.name or "chrome" in p.name)
    mcp_servers = sum(1 for p in processes if "mcp" in p.name)
    other = len(processes) - agents - browsers - mcp_servers

    return {
        "total": len(processes),
        "agents": agents,
        "browsers": browsers,
        "mcp_servers": mcp_servers,
        "other": other,
    }
