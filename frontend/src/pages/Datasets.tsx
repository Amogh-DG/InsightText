import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export const Datasets: React.FC = () => {
  const navigate = useNavigate()
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [previewDatasetId, setPreviewDatasetId] = useState<string | null>(null)

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => api.datasets.list()
  })

  const { data: previewData, isLoading: previewLoading } = useQuery({
    queryKey: ['datasetPreview', previewDatasetId],
    queryFn: () => (previewDatasetId ? api.datasets.getStoredPreview(previewDatasetId, 10) : null),
    enabled: !!previewDatasetId
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.datasets.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] })
    }
  })

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete dataset "${name}"?`)) {
      await deleteMutation.mutateAsync(id)
    }
  }

  const filtered = (datasets || []).filter((d: any) => {
    const matchesSearch = d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.source.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || d.status.toLowerCase() === statusFilter.toLowerCase()
    return matchesSearch && matchesStatus
  })

  const getStatusBadge = (status: string) => {
    const s = status.toLowerCase()
    if (s === 'ready') {
      return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#132b21] text-[#34d399]">Ready</span>
    }
    if (s === 'processing' || s === 'uploading') {
      return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#332712] text-[#fbbf24]">Processing</span>
    }
    return <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-[#3b181a] text-[#f87171]">Failed</span>
  }

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr)
      return d.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })
    } catch {
      return dateStr
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <input
            type="text"
            placeholder="Search datasets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-72 px-3.5 py-2 text-xs bg-[#191c25] border border-[#252a36] rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#4f6bf5]"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3.5 py-2 text-xs bg-[#191c25] border border-[#252a36] rounded-lg text-slate-300 focus:outline-none focus:border-[#4f6bf5]"
          >
            <option value="all">All statuses</option>
            <option value="ready">Ready</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {hasRole('analyst', 'data_scientist') && (
          <button
            onClick={() => navigate('/datasets/upload')}
            className="px-5 py-2 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors"
          >
            Upload dataset
          </button>
        )}
      </div>

      <div className="bg-[#191c25] border border-[#252a36] rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="py-20 text-center text-slate-400">Loading datasets...</div>
        ) : filtered.length === 0 ? (
          <div className="py-20 text-center text-slate-400">No datasets found</div>
        ) : (
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-[#252a36] text-[11px] text-slate-400 uppercase tracking-wider bg-[#161821]">
                <th className="py-3.5 px-6 font-medium">Name</th>
                <th className="py-3.5 px-6 font-medium">Source</th>
                <th className="py-3.5 px-6 font-medium">Rows</th>
                <th className="py-3.5 px-6 font-medium">Status</th>
                <th className="py-3.5 px-6 font-medium">Created</th>
                <th className="py-3.5 px-6 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#252a36] text-xs">
              {filtered.map((d: any) => (
                <tr key={d.id} className="hover:bg-[#1d212c] transition-colors">
                  <td className="py-4 px-6 font-medium text-slate-200">{d.name}</td>
                  <td className="py-4 px-6 text-slate-400 capitalize">{d.source}</td>
                  <td className="py-4 px-6 text-slate-300 font-mono">{d.row_count.toLocaleString()}</td>
                  <td className="py-4 px-6">{getStatusBadge(d.status)}</td>
                  <td className="py-4 px-6 text-slate-400">{formatDate(d.created_at)}</td>
                  <td className="py-4 px-6 text-right space-x-2">
                    <button
                      onClick={() => setPreviewDatasetId(d.id)}
                      className="text-slate-400 hover:text-white transition-colors"
                    >
                      View
                    </button>
                    {hasRole('analyst', 'data_scientist') && (
                      <>
                        <span className="text-slate-600">·</span>
                        <button
                          onClick={() => handleDelete(d.id, d.name)}
                          className="text-slate-400 hover:text-rose-400 transition-colors"
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {previewDatasetId && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-[#191c25] border border-[#272c3a] rounded-2xl w-full max-w-4xl p-6 shadow-2xl flex flex-col max-h-[85vh]">
            <div className="flex items-center justify-between pb-4 border-b border-[#252a36]">
              <h3 className="text-sm font-semibold text-white">Dataset Preview (First 10 Rows)</h3>
              <button
                onClick={() => setPreviewDatasetId(null)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded bg-[#252a36]"
              >
                Close
              </button>
            </div>

            <div className="flex-1 overflow-auto my-4">
              {previewLoading ? (
                <div className="py-12 text-center text-slate-400">Loading preview...</div>
              ) : previewData?.rows?.length ? (
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-[#252a36] text-[11px] text-slate-400 uppercase">
                      <th className="py-2.5 px-3">#</th>
                      {previewData.columns.map((c: string) => (
                        <th key={c} className="py-2.5 px-3">{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#252a36]">
                    {previewData.rows.map((r: any, idx: number) => (
                      <tr key={idx} className="hover:bg-[#1d212c]">
                        <td className="py-2.5 px-3 text-slate-500 font-mono">{idx + 1}</td>
                        {previewData.columns.map((c: string) => (
                          <td key={c} className="py-2.5 px-3 text-slate-300 max-w-xs truncate">
                            {r[c] !== undefined && r[c] !== null ? String(r[c]) : ''}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="py-12 text-center text-slate-400">No records available</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
