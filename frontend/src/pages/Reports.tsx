import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts'
import { api } from '../api/client'

export const Reports: React.FC = () => {
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('')
  const [dateRange, setDateRange] = useState<string>('all')

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

  const getDateBounds = (range: string) => {
    const now = new Date()
    if (range === '7d') {
      const st = new Date(now.getTime() - 7 * 86400000)
      return { startDate: st.toISOString(), endDate: now.toISOString() }
    }
    if (range === '30d') {
      const st = new Date(now.getTime() - 30 * 86400000)
      return { startDate: st.toISOString(), endDate: now.toISOString() }
    }
    if (range === '90d') {
      const st = new Date(now.getTime() - 90 * 86400000)
      return { startDate: st.toISOString(), endDate: now.toISOString() }
    }
    return { startDate: undefined, endDate: undefined }
  }

  const { startDate, endDate } = getDateBounds(dateRange)

  const { data: summary } = useQuery({
    queryKey: ['reportsSummary', selectedDatasetId, dateRange],
    queryFn: () => api.reports.summary(selectedDatasetId || undefined, startDate, endDate)
  })

  const { data: trendData } = useQuery({
    queryKey: ['trendForecastReports', selectedDatasetId],
    queryFn: () =>
      api.predict.trend({
        dataset_id: selectedDatasetId || undefined,
        target: 'negative_sentiment',
        periods: 7
      })
  })

  const handleExportCsv = () => {
    const url = api.reports.exportUrl('csv', selectedDatasetId || undefined, startDate, endDate)
    window.open(url, '_blank')
  }

  const handleExportHtml = () => {
    const url = api.reports.exportUrl('html', selectedDatasetId || undefined, startDate, endDate)
    window.open(url, '_blank')
  }

  const topicEntries = summary?.topic_sizes || []
  const categoryEntries = Object.entries(summary?.label_distribution || {})

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <select
            value={selectedDatasetId}
            onChange={(e) => setSelectedDatasetId(e.target.value)}
            className="px-3.5 py-2 text-xs bg-[#191c25] border border-[#252a36] rounded-lg text-slate-200 focus:outline-none focus:border-[#4f6bf5] min-w-[200px]"
          >
            {(datasets || []).map((d: any) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>

          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-3.5 py-2 text-xs bg-[#191c25] border border-[#252a36] rounded-lg text-slate-300 focus:outline-none focus:border-[#4f6bf5]"
          >
            <option value="all">All time</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCsv}
            className="px-4 py-2 bg-[#252a36] hover:bg-[#2e3444] text-slate-200 text-xs font-medium rounded-lg transition-colors"
          >
            Export CSV
          </button>
          <button
            onClick={handleExportHtml}
            className="px-5 py-2 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors"
          >
            Export report
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xs font-semibold text-white">Sentiment over time</h3>
            <span className="text-[11px] text-slate-500 font-mono">Forecast</span>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData?.points || summary?.trend_points || []}>
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
        </div>

        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6">
          <h3 className="text-xs font-semibold text-white mb-6">Top topics</h3>
          {topicEntries.length > 0 ? (
            <div className="flex flex-col gap-4">
              {topicEntries.slice(0, 4).map((topic: any) => (
                <div key={topic.name} className="flex flex-col gap-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300 font-medium">{topic.name}</span>
                    <span className="text-slate-400">{topic.percentage}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#252a36] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-[#4f6bf5] rounded-full"
                      style={{ width: `${topic.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="h-44 flex items-center justify-center text-xs text-slate-500">
              No topic clusters available
            </div>
          )}
        </div>

        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6">
          <h3 className="text-xs font-semibold text-white mb-6">Category breakdown</h3>
          {categoryEntries.length > 0 ? (
            <div className="flex flex-col gap-4">
              {categoryEntries.map(([label, val]: any) => (
                <div key={label} className="flex flex-col gap-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-300 font-medium">{label}</span>
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
          ) : (
            <div className="h-44 flex items-center justify-center text-xs text-slate-500">
              No category breakdown recorded
            </div>
          )}
        </div>

        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-semibold text-white mb-4">Key findings</h3>
            <ul className="flex flex-col gap-3 text-xs text-slate-300">
              {(summary?.key_findings || []).map((finding: string, idx: number) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-[#4f6bf5] text-base leading-none">•</span>
                  <span>{finding}</span>
                </li>
              ))}
              {(!summary?.key_findings || summary.key_findings.length === 0) && (
                <li className="text-slate-500">No key findings generated for this scope.</li>
              )}
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
