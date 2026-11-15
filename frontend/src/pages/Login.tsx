import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export const Login: React.FC = () => {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('priya.nair@northwind.io')
  const [password, setPassword] = useState('Password123!')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err: any) {
      setError(err.message || 'Incorrect email or password. Try again or reset your password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen w-screen flex items-center justify-center bg-[#12151b] px-4">
      <div className="w-full max-w-[420px] bg-[#1a1d26] border border-[#272c3a] rounded-2xl p-10 shadow-2xl">
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-6 h-6 rounded-md bg-[#4f6bf5]" />
            <span className="text-xl font-semibold text-white tracking-tight">InsightText</span>
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight mb-2">Welcome back</h2>
          <p className="text-xs text-slate-400">Sign in to analyze and classify your text data</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium text-slate-300">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-[#14171f] border border-[#272c3a] rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#4f6bf5] transition-colors"
            />
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-xs font-medium text-slate-300">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={`w-full px-3.5 py-2.5 bg-[#14171f] border rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none transition-colors ${
                error ? 'border-[#f87171] focus:border-[#f87171]' : 'border-[#272c3a] focus:border-[#4f6bf5]'
              }`}
            />
            {error && (
              <p className="text-xs text-[#f87171] mt-1 leading-snug">
                {error}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 mt-2 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>

          <div className="text-center mt-2">
            <button
              type="button"
              onClick={() => alert('Demo accounts:\npriya.nair@northwind.io / Password123! (Admin)\nanalyst@example.com / Analyst123!\nscientist@example.com / Scientist123!\nmanager@example.com / Manager123!\nreviewer@example.com / Reviewer123!')}
              className="text-xs text-slate-400 hover:text-slate-300 transition-colors"
            >
              Forgot password?
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
