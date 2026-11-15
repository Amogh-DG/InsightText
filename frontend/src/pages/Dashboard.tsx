import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip
} from 'recharts'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const { hasRole } = useAuth()

  const { data: summary, isLoading } = useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: () => api.reports.summary(),
    refetchInterval: 10000
  })

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center text-slate-400">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#4f6bf5]"></div>
      </div>
    )
  }

  const isEmpty = !summary || (summary.datasets_count === 0 && summary.documents_processed === 0)

  if (isEmpty) {
    return (
      <div className="flex flex-col gap-6">
        <div className="grid grid-cols-4 gap-5">
          <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-5">
            <span className="text-xs text-slate-400 font-medium">Documents processed</span>
            <div className="text-3xl font-bold text-white mt-2">0</div>
            <span className="text-xs text-slate-500 mt-2 block">No data yet</span>
          </div>

          <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-5">
            <span className="text-xs text-slate-400 font-medium">Datasets</span>
            <div className="text-3xl font-bold text-white mt-2">0</div>
            <span className="text-xs text-slate-500 mt-2 block">0 added this month</span>
          </div>

          <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-5">
            <span className="text-xs text-slate-400 font-medium">Deployed model F1</span>
            <div className="text-3xl font-bold text-slate-400 mt-2">—</div>
            <span className="text-xs text-slate-500 mt-2 block">No model deployed</span>
          </div>

          <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-5">
            <span className="text-xs text-slate-400 font-medium">Predictions today</span>
            <div className="text-3xl font-bold text-white mt-2">0</div>
            <span className="text-xs text-slate-500 mt-2 block">0% vs yesterday</span>
          </div>
        </div>

        <div className="bg-[#191c25] border border-[#252a36] rounded-xl min-h-[440px] flex flex-col items-center justify-center p-12 text-center">
          <div className="w-12 h-12 rounded-xl bg-[#2a365f] flex items-center justify-center mb-6">
            <div className="w-5 h-5 rounded bg-[#4f6bf5]" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Upload your first dataset</h2>
          <p className="text-xs text-slate-400 max-w-md mb-8">
            Add customer feedback as CSV, XLSX or JSON to see sentiment, topics and trend forecasts here.
          </p>
          <div className="flex items-center gap-3">
            {hasRole('analyst', 'data_scientist') && (
              <button
                onClick={() => navigate('/datasets/upload')}
                className="px-5 py-2.5 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors"
              >
                Upload dataset
              </button>
            )}
            <button
              onClick={() => navigate('/datasets')}
              className="px-5 py-2.5 bg-[#252a36] hover:bg-[#2e3444] text-slate-200 text-xs font-medium rounded-lg transition-colors"
            >
              View sample data
            </button>
          </div>
        </div>
      </div>
    )
  }

  const colorPalette = ['#4f6bf5', '#748ffc', '#91a7ff', '#a5b4fc', '#c7d2fe']
  const pieData = Object.entries(summary?.sentiment_distribution || {}).map(([name, val], idx) => ({
    name,
    value: val as number,
    color: colorPalette[idx % colorPalette.length]
  }))

  const labelEntries = Object.entries(summary?.label_distribution || {})
  const topicEntries = summary?.topic_sizes || []

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-4 gap-5">
        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-5">
          <span className="text-xs text-slate-400 font-medium">Documents processed</span>
          <div className="text-3xl font-bold text-white mt-2">
            {(summary.documents_processed || 0).toLocaleString()}
          </div>
          <span className={`text-xs mt-2 block ${summary.documents_delta_pct >= 0 ? 'text-[#34d399]' : 'text-[#f87171]'}`}>
            {summary.documents_delta_pct != null
              ? `${summary.documents_delta_pct >= 0 ? '+' : ''}${summary.documents_delta_pct}% this week`
              : '0% this week'}
          </span>
        </div>

        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-5">
          <span className="text-xs text-slate-400 font-medium">Datasets</span>
          <div className="text-3xl font-bold text-white mt-2">{summary.datasets_count || 0}</div>
          <span className="text-xs text-slate-400 mt-2 block">
            {summary.datasets_added_this_month ?? 0} added this month
          </span>
        </div>

        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-5">
          <span className="text-xs text-slate-400 font-medium">Deployed model F1</span>
          <div className="text-3xl font-bold text-white mt-2">
            {summary.deployed_model_f1 != null ? summary.deployed_model_f1.toFixed(2) : '—'}
          </div>
          <span className={`text-xs mt-2 block ${summary.deployed_model_f1 && summary.deployed_model_f1 >= 0.85 ? 'text-[#34d399]' : 'text-slate-400'}`}>
            {summary.deployed_model_f1 != null
              ? (summary.deployed_model_f1 >= 0.85 ? 'Target 0.85 met' : 'Target 0.85 not met')
              : 'No model deployed'}
          </span>
        </div>

        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-5">
          <span className="text-xs text-slate-400 font-medium">Predictions today</span>
          <div className="text-3xl font-bold text-white mt-2">
            {(summary.predictions_today || 0).toLocaleString()}
          </div>
          <span className={`text-xs mt-2 block ${summary.predictions_today_delta_pct >= 0 ? 'text-[#34d399]' : 'text-[#f87171]'}`}>
            {summary.predictions_today_delta_pct != null
              ? `${summary.predictions_today_delta_pct >= 0 ? '+' : ''}${summary.predictions_today_delta_pct}% vs yesterday`
              : '0% vs yesterday'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-5">
        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6">
          <h3 className="text-sm font-semibold text-white mb-6">Sentiment distribution</h3>
          {pieData.length > 0 ? (
            <div className="flex items-center justify-between">
              <div className="w-36 h-36">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      innerRadius={45}
                      outerRadius={65}
                      dataKey="value"
                      stroke="none"
                    >
                      {pieData.map((entry, idx) => (
                        <Cell key={`cell-${idx}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-col gap-3 pr-4">
                {pieData.map((p) => (
                  <div key={p.name} className="flex items-center gap-3 text-xs">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: p.color }} />
                    <span className="text-slate-300 font-medium">{p.name} {p.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-36 flex items-center justify-center text-xs text-slate-500">
              No sentiment data available
            </div>
          )}
        </div>

        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6">
          <h3 className="text-sm font-semibold text-white mb-6">Label distribution</h3>
          {labelEntries.length > 0 ? (
            <div className="flex flex-col gap-4">
              {labelEntries.map(([label, val]: any) => (
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
            <div className="h-36 flex items-center justify-center text-xs text-slate-500">
              No label categories recorded
            </div>
          )}
        </div>

        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6">
          <h3 className="text-sm font-semibold text-white mb-6">Topic size</h3>
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
            <div className="h-36 flex items-center justify-center text-xs text-slate-500">
              No topic clusters extracted
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-5">
        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-white">Sentiment trend and forecast</h3>
            <span className="text-[11px] text-slate-500 font-mono">Forecast</span>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={summary.trend_points || []}>
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
          <h3 className="text-sm font-semibold text-white mb-4">Recent low-confidence items</h3>
          <div className="overflow-x-auto">
            {summary.recent_low_confidence && summary.recent_low_confidence.length > 0 ? (
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-[#252a36] text-[11px] text-slate-400 uppercase tracking-wider">
                    <th className="pb-3 font-medium">Text</th>
                    <th className="pb-3 font-medium">Predicted</th>
                    <th className="pb-3 font-medium text-right">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#252a36] text-xs">
                  {summary.recent_low_confidence.map((item: any) => (
                    <tr key={item.id} className="hover:bg-[#1f232e] transition-colors">
                      <td className="py-3 text-slate-200 max-w-[220px] truncate pr-4">{item.text}</td>
                      <td className="py-3">
                        <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#222736] text-slate-300">
                          {item.predicted}
                        </span>
                      </td>
                      <td className="py-3 text-right text-amber-400 font-medium">
                        {item.confidence}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="py-12 text-center text-xs text-slate-500">
                No low-confidence analyses flagged
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
