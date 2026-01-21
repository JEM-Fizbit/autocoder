/**
 * Process Management Hook
 *
 * Provides state and actions for managing running processes.
 * Receives updates via WebSocket and provides API actions.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useCallback } from 'react'
import * as api from '../lib/api'
import type { ProjectProcesses, WSProcessUpdateMessage } from '../lib/types'

export interface UseProcessesReturn {
  // State
  processes: ProjectProcesses[]
  processCount: number
  isLoading: boolean
  error: Error | null

  // Actions
  killProcess: (pid: number, force?: boolean) => Promise<void>
  killAllProcesses: (force?: boolean) => Promise<void>
  pauseProcess: (pid: number) => Promise<void>
  resumeProcess: (pid: number) => Promise<void>

  // Mutations state
  isKilling: boolean
  isKillingAll: boolean

  // WebSocket update handler
  handleProcessUpdate: (message: WSProcessUpdateMessage) => void
}

export function useProcesses(): UseProcessesReturn {
  const queryClient = useQueryClient()
  const [wsProcesses, setWsProcesses] = useState<ProjectProcesses[] | null>(null)

  // Query for initial load and fallback
  const {
    data: apiProcesses,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['processes'],
    queryFn: api.listAllProcesses,
    refetchInterval: 10000, // Fallback polling every 10s
    staleTime: 5000,
  })

  // Use WebSocket data if available, otherwise API data
  const processes = wsProcesses ?? apiProcesses ?? []

  // Calculate total process count
  const processCount = processes.reduce((sum, p) => sum + p.total_count, 0)

  // Handle WebSocket process updates
  const handleProcessUpdate = useCallback((message: WSProcessUpdateMessage) => {
    setWsProcesses(message.processes)
  }, [])

  // Kill single process mutation
  const killMutation = useMutation({
    mutationFn: ({ pid, force }: { pid: number; force?: boolean }) =>
      api.killProcess(pid, force),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['processes'] })
    },
  })

  // Kill all processes mutation
  const killAllMutation = useMutation({
    mutationFn: (force?: boolean) => api.killAllProcesses(force),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['processes'] })
      setWsProcesses([]) // Immediately clear
    },
  })

  // Pause process mutation
  const pauseMutation = useMutation({
    mutationFn: (pid: number) => api.pauseProcess(pid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['processes'] })
    },
  })

  // Resume process mutation
  const resumeMutation = useMutation({
    mutationFn: (pid: number) => api.resumeProcess(pid),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['processes'] })
    },
  })

  // Action wrappers
  const killProcess = useCallback(
    async (pid: number, force?: boolean) => {
      await killMutation.mutateAsync({ pid, force })
    },
    [killMutation]
  )

  const killAllProcesses = useCallback(
    async (force?: boolean) => {
      await killAllMutation.mutateAsync(force)
    },
    [killAllMutation]
  )

  const pauseProcess = useCallback(
    async (pid: number) => {
      await pauseMutation.mutateAsync(pid)
    },
    [pauseMutation]
  )

  const resumeProcess = useCallback(
    async (pid: number) => {
      await resumeMutation.mutateAsync(pid)
    },
    [resumeMutation]
  )

  return {
    processes,
    processCount,
    isLoading,
    error: error as Error | null,
    killProcess,
    killAllProcesses,
    pauseProcess,
    resumeProcess,
    isKilling: killMutation.isPending,
    isKillingAll: killAllMutation.isPending,
    handleProcessUpdate,
  }
}
