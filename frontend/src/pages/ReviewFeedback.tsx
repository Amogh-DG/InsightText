import React, { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export const ReviewFeedback: React.FC = () => {
  const queryClient = useQueryClient()
  const { hasRole } = useAuth()
  const [filterLowConf, setFilterLowConf] = useState(true)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [correctedLabel, setCorrectedLabel] = useState('Product quality')
  const [comment, setComment] = useState('')
  const [draftTime, setDraftTime] = useState<string | null>(null)
  const [retrainMsg, setRetrainMsg] = useState<string | null>(null)

  const { data: predictions, isLoading } = useQuery({
    queryKey: ['predictionsReview', filterLowConf],
    queryFn: () => api.feedback.listPredictions(filterLowConf)
  })

  const currentItem = predictions && predictions.length > currentIndex ? predictions[currentIndex] : null
  const totalCount = predictions?.length || 0

  useEffect(() => {
    if (currentItem) {
      const savedComment = localStorage.getItem(`feedback_comment_${currentItem.id}`) || ''
      const savedLabel = localStorage.getItem(`feedback_label_${currentItem.id}`) || currentItem.predicted_label || 'Product quality'
      setComment(savedComment)
      setCorrectedLabel(savedLabel)
      const savedTime = localStorage.getItem(`feedback_time_${currentItem.id}`)
      setDraftTime(savedTime || null)
    } else {
      setComment('')
      setDraftTime(null)
    }
  }, [currentItem])

  const handleCommentChange = (val: string) => {
    setComment(val)
    if (currentItem) {
      const nowStr = new Date().toTimeString().slice(0, 5)
      localStorage.setItem(`feedback_comment_${currentItem.id}`, val)
      localStorage.setItem(`feedback_time_${currentItem.id}`, nowStr)
      setDraftTime(nowStr)
    }
  }

  const handleLabelChange = (val: string) => {
    setCorrectedLabel(val)
    if (currentItem) {
      const nowStr = new Date().toTimeString().slice(0, 5)
      localStorage.setItem(`feedback_label_${currentItem.id}`, val)
      localStorage.setItem(`feedback_time_${currentItem.id}`, nowStr)
      setDraftTime(nowStr)
    }
  }

  const submitMutation = useMutation({
    mutationFn: (predId: string) =>
      api.feedback.submit({
        prediction_id: predId,
        corrected_label: correctedLabel,
        comment: comment || undefined,
        status: 'submitted'
      }),
    onSuccess: (_, predId) => {
      localStorage.removeItem(`feedback_comment_${predId}`)
      localStorage.removeItem(`feedback_label_${predId}`)
      localStorage.removeItem(`feedback_time_${predId}`)
      queryClient.invalidateQueries({ queryKey: ['predictionsReview'] })
      queryClient.invalidateQueries({ queryKey: ['dashboardSummary'] })
      setComment('')
      setDraftTime(null)
      if (predictions && currentIndex < predictions.length - 1) {
        setCurrentIndex((prev) => prev + 1)
      }
    }
  })

  const retrainMutation = useMutation({
    mutationFn: () => api.feedback.retrain(),
    onSuccess: (data) => {
      setRetrainMsg(data?.message || 'Retraining initiated on feedback data')
      queryClient.invalidateQueries({ queryKey: ['models'] })
      setTimeout(() => setRetrainMsg(null), 5000)
    },
    onError: (err: any) => {
      setRetrainMsg(err?.message || 'Retraining failed')
      setTimeout(() => setRetrainMsg(null), 5000)
    }
  })

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

          {draftTime && (
            <span className="px-2.5 py-1 text-xs font-medium rounded-md bg-[#132c22] text-[#34d399]">
              Draft saved {draftTime}
            </span>
          )}

          {retrainMsg && (
            <span className="px-2.5 py-1 text-xs font-medium rounded-md bg-[#2a365f] text-[#93c5fd]">
              {retrainMsg}
            </span>
          )}
        </div>

        <div className="flex items-center gap-4">
          <span className="text-xs text-slate-400 font-mono">
            {totalCount} items to review
          </span>
          {hasRole('data_scientist', 'admin') && (
            <button
              onClick={() => retrainMutation.mutate()}
              disabled={retrainMutation.isPending}
              className="px-4 py-2 bg-[#252a36] hover:bg-[#2e3444] text-slate-200 text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
            >
              {retrainMutation.isPending ? 'Starting retrain...' : 'Retrain on feedback'}
            </button>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="py-20 text-center text-xs text-slate-400">Loading predictions for review...</div>
      ) : !currentItem ? (
        <div className="bg-[#191c25] border border-[#252a36] rounded-xl p-12 text-center flex flex-col items-center justify-center min-h-[360px]">
          <h3 className="text-sm font-semibold text-white mb-2">No predictions to review</h3>
          <p className="text-xs text-slate-400 max-w-sm">
            All predictions have either been verified or no inference records matched the current filter.
          </p>
        </div>
      ) : (
        <div className="bg-[#191c25] border border-[#252a36] rounded-xl overflow-hidden flex flex-col justify-between min-h-[460px]">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-mono text-slate-400">Item {currentIndex + 1} of {totalCount}</span>
              <span className="text-sm font-bold text-amber-400 font-mono">
                {Math.round(currentItem.confidence * 100)}%
              </span>
            </div>

            <div className="w-full h-72 bg-[#252a36]/50 rounded-lg border border-[#2e3444] p-4 text-xs text-slate-200 overflow-y-auto">
              {currentItem.text}
            </div>
          </div>

          <div className="p-6 border-t border-[#252a36] flex items-center justify-between bg-[#161821]">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[#1e222e] text-slate-300 border border-[#2b303e]">
                Predicted: {currentItem.predicted_label}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <select
                value={correctedLabel}
                onChange={(e) => handleLabelChange(e.target.value)}
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
                onChange={(e) => handleCommentChange(e.target.value)}
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
      )}
    </div>
  )
}
