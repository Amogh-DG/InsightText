import React, { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import { api } from '../api/client'

export const PredictTrends: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'single' | 'batch'>('single')
  const [selectedModelId, setSelectedModelId] = useState<string>('')
  const [singleText, setSingleText] = useState('Package arrived late and the box was crushed.')
  const [batchTexts, setBatchTexts] = useState(
    'Package arrived late and the box was crushed.\nCharged twice for my March subscription plan.\nApp crashes whenever I export reports.'
  )
  const [periods, setPeriods] = useState<number>(7)
  const [predictionResult, setPredictionResult] = useState<any>({
    predicted_label: 'Delivery',
    confidence: 0.89,
    probabilities: {
      Delivery: 0.89,
      Quality: 0.07,
      Billing: 0.03,
      Support: 0.01
    }
  })

  const { data: models } = useQuery({
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

  const { data: trendData } = useQuery({
    queryKey: ['trendForecast', periods],
    queryFn: () =>
      api.predict.trend({
        target: 'negative_sentiment',
        periods
      })
  })

  const predictMutation = useMutation({
    mutationFn: () => {
      if (activeTab === 'single') {
        return api.predict.single({
          model_id: selectedModelId || undefined,
          text: singleText
        })
      } else {
        const lines = batchTexts
          .split('\n')
          .map((t) => t.trim())
          .filter(Boolean)
        return api.predict.batch({
          model_id: selectedModelId || undefined,
          texts: lines
        })
      }
    },
    onSuccess: (data) => {
      if (data && data.length > 0) {
        setPredictionResult(data[0])
      }
    }
  })

  return (
    <div className="grid grid-cols-2 gap-6 items-start">
      <div className="flex flex-col gap-6">
        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6 flex flex-col gap-5">
          <div className="flex items-center gap-6 border-b border-[#252a36] pb-2 text-xs font-medium">
            <button
              onClick={() => setActiveTab('single')}
              className={`pb-2 border-b-2 transition-colors ${
                activeTab === 'single' ? 'border-[#4f6bf5] text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Single text
            </button>
            <button
              onClick={() => setActiveTab('batch')}
              className={`pb-2 border-b-2 transition-colors ${
                activeTab === 'batch' ? 'border-[#4f6bf5] text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              Batch
            </button>
          </div>

          <div className="flex flex-col gap-1.5">
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#13151b] border border-[#252a36] rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
            >
              {(models || []).map((m: any) => (
                <option key={m.id} value={m.id}>
                  {m.name} {m.version}
                </option>
              ))}
            </select>
          </div>

          {activeTab === 'single' ? (
            <textarea
              rows={4}
              value={singleText}
              onChange={(e) => setSingleText(e.target.value)}
              className="w-full p-3.5 bg-[#13151b] border border-[#252a36] rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#4f6bf5] resize-none"
            />
          ) : (
            <textarea
              rows={5}
              value={batchTexts}
              onChange={(e) => setBatchTexts(e.target.value)}
              placeholder="Enter one text per line..."
              className="w-full p-3.5 bg-[#13151b] border border-[#252a36] rounded-lg text-xs text-slate-200 focus:outline-none focus:border-[#4f6bf5] resize-none"
            />
          )}

          <button
            onClick={() => predictMutation.mutate()}
            disabled={predictMutation.isPending}
            className="w-full py-2.5 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {predictMutation.isPending ? 'Predicting...' : 'Predict'}
          </button>
        </div>

        {predictionResult && (
          <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6 flex flex-col gap-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-white">
              <span>Result ·</span>
              <span className="px-2 py-0.5 rounded text-[11px] bg-[#1d2744] text-[#748ffc] border border-[#2b3a69]">
                {predictionResult.predicted_label}
              </span>
              <span>{Math.round(predictionResult.confidence * 100)}% confidence</span>
            </div>

            <div className="flex flex-col gap-3 pt-2">
              {Object.entries(predictionResult.probabilities || {}).map(([lbl, p]: any) => {
                const pct = Math.round(Number(p) * 100)
                return (
                  <div key={lbl} className="flex flex-col gap-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-300">{lbl}</span>
                      <span className="text-slate-400 font-mono">{pct}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-[#252a36] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#4f6bf5] rounded-full"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-white">Negative sentiment forecast</h3>
          <div className="flex items-center gap-1 bg-[#13151b] p-1 rounded-lg border border-[#252a36]">
            {[7, 30, 90].map((d) => (
              <button
                key={d}
                onClick={() => setPeriods(d)}
                className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-colors ${
                  periods === d
                    ? 'bg-[#4f6bf5] text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end">
          <span className="text-[11px] text-slate-500 font-mono">Forecast</span>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={trendData?.points || []}>
              <XAxis dataKey="date" hide />
              <YAxis hide domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ backgroundColor: '#191c25', borderColor: '#2b303e', borderRadius: '8px', fontSize: '12px' }}
              />
              <Line
                type="monotone"
                dataKey="actual"
                stroke="#4f6bf5"
                strokeWidth={2.5}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="forecast"
                stroke="#4f6bf5"
                strokeWidth={2.5}
                strokeDasharray="4 4"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <p className="text-[11px] text-slate-400 mt-2">
          {trendData?.summary_text || 'Dashed line shows forecast. Expected rise of 6% next week.'}
        </p>
      </div>
    </div>
  )
}
