/**
 * Process Panel Component
 *
 * Displays all running processes grouped by project with controls to
 * pause, resume, or kill individual processes or all processes at once.
 */

import { useState } from 'react'
import {
  Activity,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Cpu,
  Globe,
  Pause,
  Play,
  Square,
  Zap,
} from 'lucide-react'
import type { ProjectProcesses, ProcessInfo } from '../lib/types'

interface ProcessPanelProps {
  processes: ProjectProcesses[]
  processCount: number
  isOpen: boolean
  onToggle: () => void
  onKillProcess: (pid: number, force?: boolean) => Promise<void>
  onKillAll: (force?: boolean) => Promise<void>
  onPauseProcess: (pid: number) => Promise<void>
  onResumeProcess: (pid: number) => Promise<void>
  isKillingAll?: boolean
}

// Process type icons and colors
function getProcessIcon(name: string) {
  if (name === 'agent') return <Cpu size={14} className="text-cyan-400" />
  if (name.includes('browser') || name.includes('chrome'))
    return <Globe size={14} className="text-blue-400" />
  if (name.includes('mcp')) return <Zap size={14} className="text-yellow-400" />
  return <Activity size={14} className="text-gray-400" />
}

function getStatusColor(status: string) {
  switch (status) {
    case 'running':
      return 'bg-green-500'
    case 'paused':
      return 'bg-yellow-500'
    case 'stopped':
      return 'bg-gray-500'
    default:
      return 'bg-gray-500'
  }
}

// Format uptime from ISO timestamp
function formatUptime(startedAt: string): string {
  try {
    const start = new Date(startedAt)
    const now = new Date()
    const diff = Math.floor((now.getTime() - start.getTime()) / 1000)

    if (diff < 60) return `${diff}s`
    if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`
    const hours = Math.floor(diff / 3600)
    const mins = Math.floor((diff % 3600) / 60)
    return `${hours}h ${mins}m`
  } catch {
    return ''
  }
}

// Single process row
function ProcessRow({
  process,
  indent = 0,
  onKill,
  onPause,
  onResume,
}: {
  process: ProcessInfo
  indent?: number
  onKill: (pid: number) => void
  onPause: (pid: number) => void
  onResume: (pid: number) => void
}) {
  const [expanded, setExpanded] = useState(true)
  const hasChildren = process.children && process.children.length > 0

  return (
    <>
      <div
        className="flex items-center gap-2 py-1.5 px-2 hover:bg-[#2a2a2a] rounded group"
        style={{ paddingLeft: `${8 + indent * 16}px` }}
      >
        {/* Expand/collapse for children */}
        {hasChildren ? (
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-0.5 hover:bg-[#333] rounded"
          >
            {expanded ? (
              <ChevronDown size={12} className="text-gray-400" />
            ) : (
              <ChevronRight size={12} className="text-gray-400" />
            )}
          </button>
        ) : (
          <span className="w-4" />
        )}

        {/* Status indicator */}
        <span className={`w-2 h-2 rounded-full ${getStatusColor(process.status)}`} />

        {/* Process icon */}
        {getProcessIcon(process.name)}

        {/* Process name */}
        <span className="font-mono text-sm text-white flex-1 truncate">
          {process.name}
        </span>

        {/* PID */}
        <span className="font-mono text-xs text-gray-500">
          PID: {process.pid}
        </span>

        {/* Uptime */}
        <span className="font-mono text-xs text-gray-500 w-16 text-right">
          {formatUptime(process.started_at)}
        </span>

        {/* Actions - visible on hover */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {process.status === 'running' ? (
            <button
              onClick={() => onPause(process.pid)}
              className="p-1 hover:bg-[#333] rounded text-yellow-400"
              title="Pause process"
            >
              <Pause size={12} />
            </button>
          ) : process.status === 'paused' ? (
            <button
              onClick={() => onResume(process.pid)}
              className="p-1 hover:bg-[#333] rounded text-green-400"
              title="Resume process"
            >
              <Play size={12} />
            </button>
          ) : null}
          <button
            onClick={() => onKill(process.pid)}
            className="p-1 hover:bg-[#333] rounded text-red-400"
            title="Kill process"
          >
            <Square size={12} />
          </button>
        </div>
      </div>

      {/* Children */}
      {hasChildren && expanded && (
        <>
          {process.children.map((child) => (
            <ProcessRow
              key={child.pid}
              process={child}
              indent={indent + 1}
              onKill={onKill}
              onPause={onPause}
              onResume={onResume}
            />
          ))}
        </>
      )}
    </>
  )
}

// Project group
function ProjectGroup({
  project,
  onKill,
  onPause,
  onResume,
}: {
  project: ProjectProcesses
  onKill: (pid: number) => void
  onPause: (pid: number) => void
  onResume: (pid: number) => void
}) {
  const [expanded, setExpanded] = useState(true)

  return (
    <div className="mb-2">
      {/* Project header */}
      <div
        className="flex items-center gap-2 py-1 px-2 cursor-pointer hover:bg-[#2a2a2a] rounded"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? (
          <ChevronDown size={14} className="text-gray-400" />
        ) : (
          <ChevronRight size={14} className="text-gray-400" />
        )}
        <span className="font-semibold text-sm text-white">{project.project_name}</span>
        <span className="px-1.5 py-0.5 text-xs bg-[#333] text-gray-400 rounded">
          {project.total_count}
        </span>
      </div>

      {/* Processes */}
      {expanded && (
        <div className="ml-2 border-l border-[#333]">
          {project.processes.length > 0 ? (
            project.processes.map((process) => (
              <ProcessRow
                key={process.pid}
                process={process}
                onKill={onKill}
                onPause={onPause}
                onResume={onResume}
              />
            ))
          ) : (
            <div className="py-2 px-4 text-gray-500 text-sm">No processes</div>
          )}
        </div>
      )}
    </div>
  )
}

export function ProcessPanel({
  processes,
  processCount,
  isOpen,
  onToggle,
  onKillProcess,
  onKillAll,
  onPauseProcess,
  onResumeProcess,
  isKillingAll,
}: ProcessPanelProps) {
  const [showKillAllConfirm, setShowKillAllConfirm] = useState(false)

  const handleKillAll = async () => {
    setShowKillAllConfirm(false)
    await onKillAll(true) // Force kill
  }

  return (
    <div
      className={`fixed right-4 bottom-14 z-30 bg-[#1a1a1a] border-3 border-black rounded-lg shadow-[4px_4px_0_0_#000] transition-all duration-200 ${
        isOpen ? 'w-96' : 'w-auto'
      }`}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 py-2 cursor-pointer border-b border-[#333]"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2">
          <Activity
            size={16}
            className={processCount > 0 ? 'text-green-400 animate-pulse' : 'text-gray-400'}
          />
          <span className="font-bold text-sm text-white">Processes</span>
          {processCount > 0 && (
            <span className="px-1.5 py-0.5 text-xs font-mono bg-green-600 text-white rounded">
              {processCount}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Kill All button */}
          {isOpen && processCount > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                setShowKillAllConfirm(true)
              }}
              disabled={isKillingAll}
              className="flex items-center gap-1 px-2 py-1 text-xs font-bold bg-red-600 hover:bg-red-700 text-white rounded border-2 border-black disabled:opacity-50"
            >
              <AlertTriangle size={12} />
              {isKillingAll ? 'Stopping...' : 'Kill All'}
            </button>
          )}
          {/* Toggle chevron */}
          {isOpen ? (
            <ChevronDown size={16} className="text-gray-400" />
          ) : (
            <ChevronRight size={16} className="text-gray-400" />
          )}
        </div>
      </div>

      {/* Content */}
      {isOpen && (
        <div className="max-h-80 overflow-y-auto p-2">
          {processes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 text-gray-500">
              <Activity size={24} className="mb-2 opacity-50" />
              <span className="text-sm">No running processes</span>
            </div>
          ) : (
            processes.map((project) => (
              <ProjectGroup
                key={project.project_name}
                project={project}
                onKill={onKillProcess}
                onPause={onPauseProcess}
                onResume={onResumeProcess}
              />
            ))
          )}
        </div>
      )}

      {/* Kill All Confirmation Modal */}
      {showKillAllConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#1a1a1a] border-3 border-black rounded-lg p-4 shadow-[4px_4px_0_0_#000] max-w-sm">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={20} className="text-red-400" />
              <span className="font-bold text-white">Emergency Stop</span>
            </div>
            <p className="text-gray-300 text-sm mb-4">
              This will forcefully terminate all {processCount} running process(es) across all projects. This cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowKillAllConfirm(false)}
                className="px-3 py-1.5 text-sm font-bold bg-[#333] hover:bg-[#444] text-white rounded border-2 border-black"
              >
                Cancel
              </button>
              <button
                onClick={handleKillAll}
                className="px-3 py-1.5 text-sm font-bold bg-red-600 hover:bg-red-700 text-white rounded border-2 border-black"
              >
                Kill All Processes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
