import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '../api/client'

export const ClassifyText: React.FC = () => {
  const navigate = useNavigate()
  const [selectedModelId, setSelectedModelId] = useState<string>('')
  const [activeTab, setActiveTab] = useState<'text' | 'dataset'>('text')
  const [inputText, setInputText] = useState(
    'I was billed twice this month and the support team has not answered my emails for a week.'
  )
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('')
  const [results, setResults] = useState<any[]>([])

  const { data: models, isLoading: modelsLoading } = useQuery({
    queryKey: ['models'],
    queryFn: async () => {
      const list = await api.models.list()
      const deployed = list.find((m: any) => m.status === 'deployed') || list[0]
      if (deployed && !selectedModelId) {
        setSelectedModelId(deployed.id)
      }
      return list
    }
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

  const classifyMutation = useMutation({
    mutationFn: () => {
      if (activeTab === 'text') {
        return api.classify.run({
          model_id: selectedModelId || undefined,
          text: inputText
        })
      } else {
        return api.classify.run({
          model_id: selectedModelId || undefined,
          dataset_id: selectedDatasetId
        })
      }
    },
    onSuccess: (data) => {
      setResults(data)
    }
  })

  const hasModels = models && models.length > 0

  return (
    <div className="grid grid-cols-2 gap-6 items-start">
      <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6 flex flex-col gap-5">
        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-slate-400">Model</label>
          <select
            value={selectedModelId}
            onChange={(e) => setSelectedModelId(e.target.value)}
            disabled={!hasModels}
            className="w-full px-3.5 py-2.5 bg-[#13151b] border border-[#252a36] rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#4f6bf5] disabled:opacity-50"
          >
            {(models || []).map((m: any) => (
              <option key={m.id} value={m.id}>
                {m.name} {m.version} {m.status === 'deployed' ? '(Deployed)' : ''}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-6 border-b border-[#252a36] pb-2 text-xs font-medium">
          <button
            onClick={() => setActiveTab('text')}
            className={`pb-2 border-b-2 transition-colors ${
              activeTab === 'text' ? 'border-[#4f6bf5] text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Paste text
          </button>
          <button
            onClick={() => setActiveTab('dataset')}
            className={`pb-2 border-b-2 transition-colors ${
              activeTab === 'dataset' ? 'border-[#4f6bf5] text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            Choose dataset
          </button>
        </div>

        {activeTab === 'text' ? (
          <div className="flex flex-col gap-4">
            <textarea
              rows={6}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Paste customer message or feedback here..."
              className="w-full p-3.5 bg-[#13151b] border border-[#252a36] rounded-lg text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#4f6bf5] resize-none"
            />
            <button
              onClick={() => classifyMutation.mutate()}
              disabled={classifyMutation.isPending || !inputText.trim() || !hasModels}
              className="w-full py-2.5 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {classifyMutation.isPending ? 'Classifying...' : 'Classify'}
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#13151b] border border-[#252a36] rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
            >
              {(datasets || []).map((d: any) => (
                <option key={d.id} value={d.id}>{d.name} ({d.row_count} rows)</option>
              ))}
            </select>
            <button
              onClick={() => classifyMutation.mutate()}
              disabled={classifyMutation.isPending || !selectedDatasetId || !hasModels}
              className="w-full py-2.5 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {classifyMutation.isPending ? 'Classifying dataset...' : 'Classify dataset'}
            </button>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-4">
        <h3 className="text-sm font-semibold text-white">Results</h3>

        {!hasModels && !modelsLoading ? (
          <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-10 flex flex-col items-center justify-center text-center">
            <h4 className="text-sm font-semibold text-white mb-2">No model exists yet</h4>
            <p className="text-xs text-slate-400 mb-6">Empty state shown when no trained model is available</p>
            <button
              onClick={() => navigate('/models/train')}
              className="px-5 py-2 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors"
            >
              Train model
            </button>
          </div>
        ) : results.length > 0 ? (
          <div className="flex flex-col gap-4">
            {results.map((r: any, idx: number) => {
              const confPct = Math.round(r.confidence * 100)
              return (
                <div key={idx} className="bg-[#191c25] border border-[#252a36] rounded-xl p-4 flex flex-col gap-3">
                  <span className="text-xs text-slate-300 font-medium truncate">{r.text}</span>
                  <div className="flex items-center gap-4">
                    <span className="px-2.5 py-1 rounded-md text-[11px] font-medium bg-[#1d2744] text-[#748ffc] border border-[#2b3a69]">
                      {r.predicted_label}
                    </span>
                    <div className="flex-1 h-2 bg-[#252a36] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#4f6bf5] rounded-full"
                        style={{ width: `${confPct}%` }}
                      />
                    </div>
                    <span className="text-xs font-bold text-white font-mono">{confPct}%</span>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-4 flex flex-col gap-3">
              <span className="text-xs text-slate-300 font-medium truncate">Billed twice this month...</span>
              <div className="flex items-center gap-4">
                <span className="px-2.5 py-1 rounded-md text-[11px] font-medium bg-[#1d2744] text-[#748ffc] border border-[#2b3a69]">
                  Billing
                </span>
                <div className="flex-1 h-2 bg-[#252a36] rounded-full overflow-hidden">
                  <div className="h-full bg-[#4f6bf5] rounded-full" style={{ width: '91%' }} />
                </div>
                <span className="text-xs font-bold text-white font-mono">91%</span>
              </div>
            </div>

            <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-4 flex flex-col gap-3">
              <span className="text-xs text-slate-300 font-medium truncate">Support team has not answered...</span>
              <div className="flex items-center gap-4">
                <span className="px-2.5 py-1 rounded-md text-[11px] font-medium bg-[#1d2744] text-[#748ffc] border border-[#2b3a69]">
                  Support
                </span>
                <div className="flex-1 h-2 bg-[#252a36] rounded-full overflow-hidden">
                  <div className="h-full bg-[#4f6bf5] rounded-full" style={{ width: '74%' }} />
                </div>
                <span className="text-xs font-bold text-white font-mono">74%</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
