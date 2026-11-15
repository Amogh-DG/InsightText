import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export const TrainModel: React.FC = () => {
  const navigate = useNavigate()
  const { hasRole } = useAuth()
  const queryClient = useQueryClient()

  const [selectedDatasetId, setSelectedDatasetId] = useState('')
  const [algorithm, setAlgorithm] = useState('XGBoost')
  const [featureType, setFeatureType] = useState('TF-IDF')
  const [testSplit, setTestSplit] = useState(20)

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

  const { data: models, isLoading: modelsLoading } = useQuery({
    queryKey: ['models'],
    queryFn: () => api.models.list(),
    refetchInterval: 3000
  })

  const trainMutation = useMutation({
    mutationFn: () =>
      api.models.train({
        dataset_id: selectedDatasetId,
        algorithm,
        feature_type: featureType,
        test_split: testSplit / 100
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] })
    }
  })

  const activeTraining = models?.find((m: any) => m.status === 'training')

  const getStatusBadge = (status: string, f1?: number) => {
    if (status === 'training') {
      return <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#332712] text-[#fbbf24]">Training</span>
    }
    if (status === 'failed') {
      return <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#3b181a] text-[#f87171]">Failed</span>
    }
    if (f1 !== undefined && f1 < 0.85) {
      return <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#3b181a] text-[#f87171]">Below target</span>
    }
    return <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#132c22] text-[#34d399]">Done</span>
  }

  return (
    <div className="grid grid-cols-2 gap-6 items-start">
      <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6 flex flex-col gap-5">
        <h3 className="text-sm font-semibold text-white">New training run</h3>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-slate-400">Dataset</label>
          <select
            value={selectedDatasetId}
            onChange={(e) => setSelectedDatasetId(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-[#13151b] border border-[#252a36] rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
          >
            {(datasets || []).map((d: any) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-xs font-medium text-slate-400">Algorithm</label>
          <select
            value={algorithm}
            onChange={(e) => setAlgorithm(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-[#13151b] border border-[#252a36] rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
          >
            <option value="XGBoost">XGBoost</option>
            <option value="Random Forest">Random Forest</option>
            <option value="Logistic Regression">Logistic Regression</option>
          </select>
        </div>

        <div className="flex flex-col gap-2">
          <label className="text-xs font-medium text-slate-400">Feature type</label>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setFeatureType('TF-IDF')}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition-colors ${
                featureType === 'TF-IDF'
                  ? 'bg-[#4f6bf5] text-white'
                  : 'bg-[#13151b] text-slate-400 border border-[#252a36]'
              }`}
            >
              TF-IDF
            </button>
            <button
              type="button"
              onClick={() => setFeatureType('BERT embeddings')}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition-colors ${
                featureType === 'BERT embeddings'
                  ? 'bg-[#4f6bf5] text-white'
                  : 'bg-[#13151b] text-slate-400 border border-[#252a36]'
              }`}
            >
              BERT embeddings
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400 font-medium">Test split: {testSplit}%</span>
          </div>
          <input
            type="range"
            min={10}
            max={40}
            step={5}
            value={testSplit}
            onChange={(e) => setTestSplit(Number(e.target.value))}
            className="w-full accent-[#4f6bf5] bg-[#252a36] rounded-lg h-1.5 cursor-pointer"
          />
        </div>

        {hasRole('data_scientist') ? (
          <button
            onClick={() => trainMutation.mutate()}
            disabled={trainMutation.isPending || !!activeTraining || !selectedDatasetId}
            className="w-full py-2.5 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50 mt-2"
          >
            {trainMutation.isPending || activeTraining ? 'Training in progress...' : 'Train model'}
          </button>
        ) : (
          <div className="text-center py-2 text-xs text-slate-500">
            Data scientist role required to start training runs
          </div>
        )}
      </div>

      <div className="flex flex-col gap-6">
        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-white">Training progress</h3>
            <span className="text-xs text-slate-400 font-mono">
              {activeTraining ? 'Epoch 6 of 10' : 'Idle'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-2.5 py-0.5 rounded text-[11px] font-medium bg-[#332712] text-[#fbbf24]">
              {activeTraining ? 'Training' : 'Ready'}
            </span>
          </div>

          <div className="w-full h-2 bg-[#252a36] rounded-full overflow-hidden mt-1">
            <div
              className={`h-full bg-[#4f6bf5] rounded-full transition-all duration-500 ${
                activeTraining ? 'w-3/5 animate-pulse' : 'w-full'
              }`}
            />
          </div>

          <span className="text-[11px] text-slate-500">
            {activeTraining ? 'Estimated 3 min remaining' : 'No active training runs'}
          </span>
        </div>

        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6 flex flex-col gap-4">
          <h3 className="text-xs font-semibold text-white">Recent runs</h3>
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#252a36] text-[11px] text-slate-400 uppercase">
                <th className="pb-3">Run</th>
                <th className="pb-3">Algorithm</th>
                <th className="pb-3">F1</th>
                <th className="pb-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#252a36]">
              {modelsLoading ? (
                <tr>
                  <td colSpan={4} className="py-6 text-center text-slate-400">Loading models...</td>
                </tr>
              ) : (models || []).length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-6 text-center text-slate-400">No training runs yet</td>
                </tr>
              ) : (
                (models || []).map((m: any) => {
                  const f1 = m.metrics?.f1 !== undefined ? m.metrics.f1 : undefined
                  return (
                    <tr
                      key={m.id}
                      onClick={() => navigate(`/models/evaluate?id=${m.id}`)}
                      className="hover:bg-[#1f232e] cursor-pointer transition-colors"
                    >
                      <td className="py-3 font-mono text-slate-200">{m.version}</td>
                      <td className="py-3 text-slate-300">{m.algorithm}</td>
                      <td className="py-3 font-mono text-slate-300">{f1 !== undefined ? f1.toFixed(2) : '—'}</td>
                      <td className="py-3 text-right">{getStatusBadge(m.status, f1)}</td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
