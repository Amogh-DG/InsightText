import React, { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export const AdminModels: React.FC = () => {
  const queryClient = useQueryClient()
  const [threshold, setThreshold] = useState<number>(0.6)
  const [intentsInput, setIntentsInput] = useState<string>('complaint, inquiry, praise, request, suggestion, other')
  const [settingsLoaded, setSettingsLoaded] = useState(false)

  const { data: models, isLoading } = useQuery({
    queryKey: ['adminModels'],
    queryFn: () => api.models.list()
  })

  useQuery({
    queryKey: ['systemSettings'],
    queryFn: async () => {
      const data = await api.settings.get()
      if (data && !settingsLoaded) {
        setThreshold(data.confidence_threshold)
        setIntentsInput(data.intent_labels.join(', '))
        setSettingsLoaded(true)
      }
      return data
    }
  })

  const deployMutation = useMutation({
    mutationFn: (id: string) => api.models.deploy(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminModels'] })
      queryClient.invalidateQueries({ queryKey: ['models'] })
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.models.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminModels'] })
      queryClient.invalidateQueries({ queryKey: ['models'] })
    }
  })

  const saveSettingsMutation = useMutation({
    mutationFn: () => {
      const list = intentsInput.split(',').map((s) => s.trim()).filter(Boolean)
      return api.settings.update({
        confidence_threshold: threshold,
        intent_labels: list
      })
    },
    onSuccess: () => {
      alert('System settings updated successfully')
      queryClient.invalidateQueries({ queryKey: ['systemSettings'] })
    }
  })

  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase()
    if (s === 'deployed') {
      return <span className="px-2.5 py-0.5 rounded text-[11px] font-medium bg-[#132c22] text-[#34d399]">Deployed</span>
    }
    if (s === 'archived') {
      return <span className="px-2.5 py-0.5 rounded text-[11px] font-medium bg-[#252a36] text-slate-400">Archived</span>
    }
    return <span className="px-2.5 py-0.5 rounded text-[11px] font-medium bg-[#1d2744] text-[#748ffc]">Trained</span>
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-6 border-b border-[#252a36] pb-2 text-xs font-medium">
        <NavLink
          to="/admin/users"
          className="pb-2 border-b-2 border-transparent text-slate-400 hover:text-slate-200 transition-colors"
        >
          Users
        </NavLink>
        <NavLink
          to="/admin/models"
          className="pb-2 border-b-2 border-[#4f6bf5] text-white transition-colors"
        >
          Models & Settings
        </NavLink>
      </div>

      <div className="bg-[#191c25] border border-[#252a36] rounded-xl overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-[#252a36] text-[11px] text-slate-400 uppercase bg-[#161821]">
              <th className="py-3.5 px-6 font-medium">Name</th>
              <th className="py-3.5 px-6 font-medium">Algorithm</th>
              <th className="py-3.5 px-6 font-medium">Version</th>
              <th className="py-3.5 px-6 font-medium">F1</th>
              <th className="py-3.5 px-6 font-medium">Status</th>
              <th className="py-3.5 px-6 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#252a36]">
            {isLoading ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-400">Loading models...</td>
              </tr>
            ) : (models || []).length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-400">No models found</td>
              </tr>
            ) : (
              (models || []).map((m: any) => {
                const f1 = m.metrics?.f1 !== undefined ? m.metrics.f1 : null
                return (
                  <tr key={m.id} className="hover:bg-[#1d212c] transition-colors">
                    <td className="py-4 px-6 font-medium text-slate-200">{m.name}</td>
                    <td className="py-4 px-6 text-slate-400">{m.algorithm}</td>
                    <td className="py-4 px-6 text-slate-300 font-mono">{m.version}</td>
                    <td className="py-4 px-6 text-slate-300 font-mono">{f1 !== null ? f1.toFixed(2) : '—'}</td>
                    <td className="py-4 px-6">{getStatusBadge(m.status)}</td>
                    <td className="py-4 px-6 text-right space-x-2">
                      {m.status !== 'deployed' && (
                        <>
                          <button
                            onClick={() => deployMutation.mutate(m.id)}
                            className="text-slate-400 hover:text-white transition-colors"
                          >
                            Deploy
                          </button>
                          <span className="text-slate-600">·</span>
                        </>
                      )}
                      <button
                        onClick={() => {
                          if (confirm(`Delete model ${m.name} ${m.version}?`)) {
                            deleteMutation.mutate(m.id)
                          }
                        }}
                        className="text-slate-400 hover:text-rose-400 transition-colors"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6 flex flex-col gap-5 max-w-2xl">
        <h3 className="text-sm font-semibold text-white">System Settings</h3>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-slate-400">Low confidence threshold</label>
          <input
            type="number"
            step="0.05"
            min="0.1"
            max="1.0"
            value={threshold}
            onChange={(e) => setThreshold(parseFloat(e.target.value))}
            className="w-48 px-3.5 py-2 text-xs bg-[#13151b] border border-[#252a36] rounded-lg text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-slate-400">Configured intent labels (comma-separated)</label>
          <textarea
            rows={3}
            value={intentsInput}
            onChange={(e) => setIntentsInput(e.target.value)}
            className="w-full p-3.5 text-xs bg-[#13151b] border border-[#252a36] rounded-lg text-slate-200 focus:outline-none focus:border-[#4f6bf5] resize-none"
          />
        </div>

        <div>
          <button
            onClick={() => saveSettingsMutation.mutate()}
            disabled={saveSettingsMutation.isPending}
            className="px-5 py-2 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {saveSettingsMutation.isPending ? 'Saving...' : 'Save settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
