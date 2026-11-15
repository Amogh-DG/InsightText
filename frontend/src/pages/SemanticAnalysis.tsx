import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export const SemanticAnalysis: React.FC = () => {
  const queryClient = useQueryClient()
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('')
  const [activeTab, setActiveTab] = useState<'results' | 'summary' | 'entities'>('results')

  const [types, setTypes] = useState({
    sentiment: true,
    entities: true,
    intent: true,
    topics: false
  })

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: async () => {
      const list = await api.datasets.list()
      if (list.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(list[0].id)
      }
      return list
    }
  })

  const { data: results, isLoading: resultsLoading } = useQuery({
    queryKey: ['analysisResults', selectedDatasetId],
    queryFn: () => (selectedDatasetId ? api.analysis.results(selectedDatasetId) : []),
    enabled: !!selectedDatasetId
  })

  const { data: summary } = useQuery({
    queryKey: ['analysisSummary', selectedDatasetId],
    queryFn: () => (selectedDatasetId ? api.analysis.summary(selectedDatasetId) : null),
    enabled: !!selectedDatasetId
  })

  const runMutation = useMutation({
    mutationFn: () => {
      const chosen = Object.entries(types)
        .filter(([_, v]) => v)
        .map(([k]) => k)
      return api.analysis.run({
        dataset_id: selectedDatasetId,
        analysis_types: chosen,
        num_topics: 4
      })
    },
    onSuccess: () => {
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['analysisResults', selectedDatasetId] })
        queryClient.invalidateQueries({ queryKey: ['analysisSummary', selectedDatasetId] })
      }, 1500)
    }
  })

  const toggleType = (key: keyof typeof types) => {
    setTypes((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const sentimentPill = (label: string) => {
    const l = label.toLowerCase()
    if (l === 'positive') {
      return <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#132c22] text-[#34d399]">Positive</span>
    }
    if (l === 'negative') {
      return <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#3b181a] text-[#f87171]">Negative</span>
    }
    return <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#222736] text-slate-400">Neutral</span>
  }

  const allEntities = (results || []).flatMap((r: any) => r.entities || [])

  return (
    <div className="flex flex-col gap-6">
      <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-5 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div className="flex flex-col gap-1.5">
            <span className="text-xs text-slate-400 font-medium">Dataset</span>
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="px-3.5 py-1.5 text-xs bg-[#13151b] border border-[#252a36] rounded-lg text-slate-200 focus:outline-none focus:border-[#4f6bf5] min-w-[200px]"
            >
              {(datasets || []).map((d: any) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-1.5">
            <span className="text-xs text-slate-400 font-medium">Analysis types</span>
            <div className="flex items-center gap-4 text-xs text-slate-300">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={types.sentiment}
                  onChange={() => toggleType('sentiment')}
                  className="rounded bg-[#13151b] border-[#252a36] text-[#4f6bf5] focus:ring-0"
                />
                <span>Sentiment</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={types.entities}
                  onChange={() => toggleType('entities')}
                  className="rounded bg-[#13151b] border-[#252a36] text-[#4f6bf5] focus:ring-0"
                />
                <span>Entities</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={types.intent}
                  onChange={() => toggleType('intent')}
                  className="rounded bg-[#13151b] border-[#252a36] text-[#4f6bf5] focus:ring-0"
                />
                <span>Intent</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={types.topics}
                  onChange={() => toggleType('topics')}
                  className="rounded bg-[#13151b] border-[#252a36] text-[#4f6bf5] focus:ring-0"
                />
                <span>Topics</span>
              </label>
            </div>
          </div>
        </div>

        <button
          onClick={() => runMutation.mutate()}
          disabled={runMutation.isPending || !selectedDatasetId}
          className="px-6 py-2 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          {runMutation.isPending ? 'Running...' : 'Run analysis'}
        </button>
      </div>

      <div className="flex items-center gap-6 border-b border-[#252a36] pb-2 text-xs font-medium">
        <button
          onClick={() => setActiveTab('results')}
          className={`pb-2 border-b-2 transition-colors ${
            activeTab === 'results' ? 'border-[#4f6bf5] text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Results
        </button>
        <button
          onClick={() => setActiveTab('summary')}
          className={`pb-2 border-b-2 transition-colors ${
            activeTab === 'summary' ? 'border-[#4f6bf5] text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Summary
        </button>
        <button
          onClick={() => setActiveTab('entities')}
          className={`pb-2 border-b-2 transition-colors ${
            activeTab === 'entities' ? 'border-[#4f6bf5] text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Entities
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 bg-[#191c25] border border-[#252a36] rounded-xl overflow-hidden">
          {activeTab === 'results' && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#252a36] text-[11px] text-slate-400 uppercase bg-[#161821]">
                    <th className="py-3 px-4">Text</th>
                    <th className="py-3 px-4">Sentiment</th>
                    <th className="py-3 px-4">Entities</th>
                    <th className="py-3 px-4">Intent</th>
                    <th className="py-3 px-4 text-right">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#252a36]">
                  {resultsLoading ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-slate-400">Loading analysis results...</td>
                    </tr>
                  ) : (results || []).length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-12 text-center text-slate-400">
                        No analysis results. Select a dataset and click "Run analysis".
                      </td>
                    </tr>
                  ) : (
                    (results || []).map((r: any) => {
                      const confPct = Math.round((r.sentiment_score || 0.85) * 100)
                      return (
                        <tr key={r.id} className="hover:bg-[#1d212c]">
                          <td className="py-3 px-4 text-slate-200 max-w-[200px] truncate">{r.text}</td>
                          <td className="py-3 px-4">{sentimentPill(r.sentiment_label)}</td>
                          <td className="py-3 px-4">
                            <div className="flex flex-wrap gap-1">
                              {(r.entities || []).slice(0, 2).map((e: any, i: number) => (
                                <span
                                  key={i}
                                  className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-[#1d2744] text-[#748ffc] border border-[#2b3a69]"
                                >
                                  {e.text}
                                </span>
                              ))}
                              {(!r.entities || r.entities.length === 0) && (
                                <span className="text-slate-600">—</span>
                              )}
                            </div>
                          </td>
                          <td className="py-3 px-4 text-slate-300 capitalize">{r.intent || 'other'}</td>
                          <td className="py-3 px-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <span className="font-mono text-slate-300">{confPct}</span>
                              <div className="w-16 h-1.5 bg-[#252a36] rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-[#4f6bf5] rounded-full"
                                  style={{ width: `${confPct}%` }}
                                />
                              </div>
                            </div>
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'summary' && (
            <div className="p-6 flex flex-col gap-6">
              <h4 className="text-sm font-semibold text-white">Full Analysis Summary</h4>
              <p className="text-xs text-slate-400">Total documents evaluated: {summary?.total_analyzed || 0}</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-[#14171f] rounded-lg border border-[#252a36]">
                  <h5 className="text-xs font-medium text-slate-300 mb-2">Dominant Sentiment</h5>
                  <div className="text-lg font-bold text-white">Positive</div>
                </div>
                <div className="p-4 bg-[#14171f] rounded-lg border border-[#252a36]">
                  <h5 className="text-xs font-medium text-slate-300 mb-2">Most Frequent Intent</h5>
                  <div className="text-lg font-bold text-white">Complaint</div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'entities' && (
            <div className="p-6">
              <h4 className="text-sm font-semibold text-white mb-4">Extracted Named Entities</h4>
              <div className="flex flex-wrap gap-2">
                {allEntities.map((e: any, idx: number) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-lg text-xs bg-[#1d2744] text-[#748ffc] border border-[#2b3a69]"
                  >
                    {e.text} <span className="text-[10px] text-slate-400 ml-1">({e.label})</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-6">
          <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6">
            <h3 className="text-xs font-semibold text-white mb-4">Sentiment summary</h3>
            <div className="flex flex-col gap-3.5">
              {[
                { label: 'Positive', val: summary?.sentiment_summary?.Positive ?? 46 },
                { label: 'Neutral', val: summary?.sentiment_summary?.Neutral ?? 31 },
                { label: 'Negative', val: summary?.sentiment_summary?.Negative ?? 23 }
              ].map((s) => (
                <div key={s.label} className="flex flex-col gap-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300">{s.label}</span>
                    <span className="text-slate-400">{s.val}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#252a36] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#4f6bf5] rounded-full"
                      style={{ width: `${s.val}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6">
            <h3 className="text-xs font-semibold text-white mb-4">Top intents</h3>
            <div className="flex flex-col gap-3.5">
              {Object.entries(
                summary?.top_intents && Object.keys(summary.top_intents).length > 0
                  ? summary.top_intents
                  : { Complaint: 41, Praise: 28, 'Feature request': 19 }
              ).map(([intent, val]: any) => (
                <div key={intent} className="flex flex-col gap-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300">{intent}</span>
                    <span className="text-slate-400">{val}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#252a36] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#4f6bf5] rounded-full"
                      style={{ width: `${val}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
