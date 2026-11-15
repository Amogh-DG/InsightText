import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export const ReviewFeedback: React.FC = () => {
  const queryClient = useQueryClient()
  const [filterLowConf, setFilterLowConf] = useState(true)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [correctedLabel, setCorrectedLabel] = useState('Product quality')
  const [comment, setComment] = useState('')
  const [draftTime, setDraftTime] = useState('10:42')

  const { data: predictions } = useQuery({
    queryKey: ['predictionsReview', filterLowConf],
    queryFn: () => api.feedback.listPredictions(filterLowConf)
  })

  const submitMutation = useMutation({
    mutationFn: (predId: string) =>
      api.feedback.submit({
        prediction_id: predId,
        corrected_label: correctedLabel,
        comment,
        status: 'submitted'
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['predictionsReview'] })
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] })
      setComment('')
      if (predictions && currentIndex < predictions.length - 1) {
        setCurrentIndex((prev) => prev + 1)
      }
    }
  })

  const currentItem = predictions?.[currentIndex] || {
    id: 'mock-1',
    text: 'Delivery was late but the driver was kind',
    predicted_label: 'Delivery',
    confidence: 0.58
  }

  const totalCount = predictions?.length || 128

  const handleCommentChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setComment(e.target.value)
    const now = new Date()
    setDraftTime(now.toTimeString().slice(0, 5))
  }

  return (
    <div className="flex flex-col gap-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <select
            value={filterLowConf ? 'low' : 'all'}
            onChange={(e) => {
              setFilterLowConf(e.target.value === 'low')
              setCurrentIndex(0)
            }}
            className="px-3.5 py-2 text-xs bg-[#191c25] border border-[#252a36] rounded-lg text-slate-300 focus:outline-none focus:border-[#4f6bf5]"
          >
            <option value="low">Low confidence only</option>
            <option value="all">All predictions</option>
          </select>

          <span className="px-2.5 py-1 text-xs font-medium rounded-md bg-[#132c22] text-[#34d399]">
            Draft saved {draftTime}
          </span>
        </div>

        <span className="text-xs text-slate-400 font-mono">
          {totalCount} items to review
        </span>
      </div>

      <div className="bg-[#191c25] border border-[#252a36] rounded-xl overflow-hidden flex flex-col justify-between min-h-[460px]">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-white">{currentItem.text}</h3>
            <span className="text-sm font-bold text-amber-400 font-mono">
              {Math.round(currentItem.confidence * 100)}%
            </span>
          </div>

          <div className="w-full h-72 bg-[#252a36]/50 rounded-lg border border-[#2e3444] p-4 text-xs text-slate-400">
            {currentItem.text}
          </div>
        </div>

        <div className="p-6 border-t border-[#252a36] flex items-center justify-between bg-[#161821]">
          <div className="flex items-center gap-3">
            <span className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1e222e] text-slate-300 border border-[#2b303e]">
              {currentItem.predicted_label}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={correctedLabel}
              onChange={(e) => setCorrectedLabel(e.target.value)}
              className="px-3.5 py-2 text-xs bg-[#191c25] border border-[#252a36] rounded-lg text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
            >
              <option value="Billing">Billing</option>
              <option value="Delivery">Delivery</option>
              <option value="Product quality">Product quality</option>
              <option value="Support">Support</option>
            </select>

            <input
              type="text"
              placeholder="Add a comment..."
              value={comment}
              onChange={handleCommentChange}
              className="w-56 px-3.5 py-2 text-xs bg-[#191c25] border border-[#252a36] rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#4f6bf5]"
            />

            <button
              onClick={() => submitMutation.mutate(currentItem.id)}
              disabled={submitMutation.isPending}
              className="px-6 py-2 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {submitMutation.isPending ? 'Submitting...' : 'Submit'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
