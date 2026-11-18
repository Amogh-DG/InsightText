import React, { useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LogOut, Network } from 'lucide-react'

export const Layout: React.FC = () => {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', roles: ['analyst', 'data_scientist', 'manager', 'reviewer', 'admin'] },
    { label: 'Datasets', path: '/datasets', roles: ['analyst', 'data_scientist', 'manager', 'reviewer', 'admin'] },
    { label: 'Semantic Analysis', path: '/analysis', roles: ['analyst', 'data_scientist', 'admin'] },
    { label: 'Classify', path: '/classify', roles: ['analyst', 'data_scientist', 'admin'] },
    { label: 'Models', path: '/models', roles: ['analyst', 'data_scientist', 'manager', 'reviewer', 'admin'] },
    { label: 'Predict', path: '/predict', roles: ['analyst', 'data_scientist', 'manager', 'admin'] },
    { label: 'Review', path: '/review', roles: ['reviewer', 'analyst', 'data_scientist', 'admin'] },
    { label: 'Reports', path: '/reports', roles: ['analyst', 'data_scientist', 'manager', 'reviewer', 'admin'] }
  ]

  const getPageTitle = () => {
    const p = location.pathname
    if (p.startsWith('/graph') || p.startsWith('/admin/graph')) return 'Insight Graph'
    if (p.startsWith('/dashboard')) return 'Dashboard'
    if (p === '/datasets/upload') return 'Upload data'
    if (p.startsWith('/datasets')) return 'Datasets'
    if (p.startsWith('/analysis')) return 'Semantic analysis'
    if (p.startsWith('/classify')) return 'Classify text'
    if (p.startsWith('/models/evaluate')) return 'Model evaluation'
    if (p.startsWith('/models/train')) return 'Train model'
    if (p.startsWith('/models')) return 'Train model'
    if (p.startsWith('/predict')) return 'Predict trends'
    if (p.startsWith('/review')) return 'Review feedback'
    if (p.startsWith('/reports')) return 'Reports'
    if (p.startsWith('/admin/models')) return 'Admin · Models'
    if (p.startsWith('/admin')) return 'Admin · Users'
    return 'InsightText'
  }

  const getInitials = (name?: string) => {
    if (!name) return 'U'
    const parts = name.split(' ')
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
    return name.slice(0, 2).toUpperCase()
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      navigate(`/predict?q=${encodeURIComponent(searchQuery.trim())}`)
    }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#12151b] text-slate-100">
      <aside className="w-64 flex-shrink-0 border-r border-[#1f232e] bg-[#12151b] flex flex-col justify-between p-5">
        <div>
          <div className="flex items-center gap-3 px-3 py-2 mb-8">
            <div className="w-5 h-5 rounded bg-[#4f6bf5]" />
            <span className="font-semibold text-lg text-white tracking-tight">InsightText</span>
          </div>

          <nav className="flex flex-col gap-1">
            {navItems.map((item) => {
              if (item.roles && user && user.role !== 'admin' && !item.roles.includes(user.role)) {
                return null
              }
              const isActive = location.pathname.startsWith(item.path)
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-[#4f6bf5] text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#1a1e28]'
                  }`}
                >
                  {item.label}
                </NavLink>
              )
            })}

            {user?.role === 'admin' && (
              <div className="mt-5 pt-3 border-t border-[#1f232e] flex flex-col gap-1">
                <div className="px-4 py-1 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                  ADMIN
                </div>
                <NavLink
                  to="/admin/users"
                  className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    location.pathname.startsWith('/admin')
                      ? 'bg-[#1e2338] text-[#818cf8] border border-[#2e3760]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#1a1e28]'
                  }`}
                >
                  Admin
                </NavLink>
                <NavLink
                  to="/graph"
                  className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center justify-between ${
                    location.pathname.startsWith('/graph')
                      ? 'bg-[#1e2338] text-[#818cf8] border border-[#2e3760]'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#1a1e28]'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Network size={16} className="text-[#818cf8]" />
                    <span>Insight Graph</span>
                  </div>
                  <span className="text-[10px] font-medium px-1.5 py-0.5 rounded bg-[#252d4a] text-[#818cf8] border border-[#374271]">
                    Admin
                  </span>
                </NavLink>
              </div>
            )}
          </nav>
        </div>

        <div className="pt-4 border-t border-[#1f232e]">
          <button
            onClick={logout}
            className="flex items-center gap-2 w-full px-4 py-2 text-sm text-slate-400 hover:text-rose-400 rounded-lg hover:bg-[#1a1e28] transition-colors"
          >
            <LogOut size={16} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 border-b border-[#1f232e] bg-[#12151b] flex items-center justify-between px-8">
          <h1 className="text-xl font-semibold text-white tracking-tight">{getPageTitle()}</h1>

          <div className="flex items-center gap-4">
            <form onSubmit={handleSearchSubmit} className="relative">
              <input
                type="text"
                placeholder="Search documents, models..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-64 px-3.5 py-1.5 text-xs bg-[#191c25] border border-[#262b37] rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#4f6bf5]"
              />
            </form>

            <div className="px-2.5 py-1 text-xs text-slate-400 bg-[#191c25] border border-[#262b37] rounded-md font-mono">
              3
            </div>

            <div className="flex items-center gap-3 pl-2">
              <div className="w-8 h-8 rounded-full bg-[#243261] text-[#718aff] flex items-center justify-center text-xs font-bold border border-[#3b4d8c]">
                {getInitials(user?.name)}
              </div>
              <div className="flex flex-col text-left">
                <span className="text-xs font-medium text-slate-200 leading-tight">{user?.name || 'User'}</span>
                <span className="text-[11px] text-slate-500 capitalize leading-tight">{user?.role || 'Guest'}</span>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8 bg-[#12151b]">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
