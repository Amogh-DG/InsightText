import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'

export const AdminUsers: React.FC = () => {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingUserId, setEditingUserId] = useState<string | null>(null)

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('analyst')
  const [password, setPassword] = useState('Password123!')

  const { data: users, isLoading } = useQuery({
    queryKey: ['adminUsers'],
    queryFn: () => api.users.list()
  })

  const createMutation = useMutation({
    mutationFn: () => api.users.create({ name, email, role, password }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] })
      closeModal()
    }
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: string; body: any }) => api.users.update(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] })
      closeModal()
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.users.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] })
    }
  })

  const openAddModal = () => {
    setEditingUserId(null)
    setName('')
    setEmail('')
    setRole('analyst')
    setPassword('Password123!')
    setIsModalOpen(true)
  }

  const openEditModal = (u: any) => {
    setEditingUserId(u.id)
    setName(u.name)
    setEmail(u.email)
    setRole(u.role)
    setIsModalOpen(true)
  }

  const closeModal = () => {
    setIsModalOpen(false)
    setEditingUserId(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingUserId) {
      updateMutation.mutate({ id: editingUserId, body: { name, email, role } })
    } else {
      createMutation.mutate()
    }
  }

  const toggleUserActive = (u: any) => {
    updateMutation.mutate({ id: u.id, body: { is_active: !u.is_active } })
  }

  const filteredUsers = (users || []).filter((u: any) =>
    u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.role.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <input
            type="text"
            placeholder="Search users..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-72 px-3.5 py-2 text-xs bg-[#191c25] border border-[#252a36] rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-[#4f6bf5]"
          />
          <span className="text-xs text-slate-400">
            Admin: full access · Analyst: run and review · Viewer: read only
          </span>
        </div>

        <button
          onClick={openAddModal}
          className="px-5 py-2 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors"
        >
          Add user
        </button>
      </div>

      <div className="bg-[#191c25] border border-[#252a36] rounded-xl overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-[#252a36] text-[11px] text-slate-400 uppercase bg-[#161821]">
              <th className="py-3.5 px-6 font-medium">Name</th>
              <th className="py-3.5 px-6 font-medium">Email</th>
              <th className="py-3.5 px-6 font-medium">Role</th>
              <th className="py-3.5 px-6 font-medium">Status</th>
              <th className="py-3.5 px-6 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#252a36]">
            {isLoading ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-slate-400">Loading users...</td>
              </tr>
            ) : filteredUsers.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-12 text-center text-slate-400">No users found</td>
              </tr>
            ) : (
              filteredUsers.map((u: any) => (
                <tr key={u.id} className="hover:bg-[#1d212c] transition-colors">
                  <td className="py-4 px-6 font-medium text-slate-200">{u.name}</td>
                  <td className="py-4 px-6 text-slate-400">{u.email}</td>
                  <td className="py-4 px-6">
                    <span className="px-2.5 py-1 rounded-md text-[11px] font-medium bg-[#1d212c] text-slate-300 border border-[#2b303e] capitalize">
                      {u.role.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <button
                      onClick={() => toggleUserActive(u)}
                      className="flex items-center gap-2 hover:opacity-80 transition-opacity"
                    >
                      <span className="text-slate-300 capitalize">{u.is_active ? 'Active' : 'Inactive'}</span>
                      <span className={`w-2 h-2 rounded-full ${u.is_active ? 'bg-[#34d399]' : 'border border-slate-500'}`} />
                    </button>
                  </td>
                  <td className="py-4 px-6 text-right space-x-2">
                    <button
                      onClick={() => openEditModal(u)}
                      className="text-slate-400 hover:text-white transition-colors"
                    >
                      Edit
                    </button>
                    <span className="text-slate-600">·</span>
                    <button
                      onClick={() => {
                        if (confirm(`Remove user ${u.email}?`)) {
                          deleteMutation.mutate(u.id)
                        }
                      }}
                      className="text-slate-400 hover:text-rose-400 transition-colors"
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-[#191c25] border border-[#272c3a] rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <h3 className="text-sm font-semibold text-white mb-6">
              {editingUserId ? 'Edit user' : 'Add user'}
            </h3>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-slate-400">Full name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ana Costa"
                  className="w-full px-3.5 py-2 text-xs bg-[#13151b] border border-[#252a36] rounded-lg text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-slate-400">Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ana.costa@northwind.io"
                  className="w-full px-3.5 py-2 text-xs bg-[#13151b] border border-[#252a36] rounded-lg text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
                />
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs font-medium text-slate-400">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full px-3.5 py-2 text-xs bg-[#13151b] border border-[#252a36] rounded-lg text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
                >
                  <option value="analyst">Analyst</option>
                  <option value="data_scientist">Data Scientist</option>
                  <option value="manager">Manager</option>
                  <option value="reviewer">Reviewer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              {!editingUserId && (
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-medium text-slate-400">Password</label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3.5 py-2 text-xs bg-[#13151b] border border-[#252a36] rounded-lg text-slate-200 focus:outline-none focus:border-[#4f6bf5]"
                  />
                </div>
              )}

              <div className="flex items-center justify-end gap-3 mt-4">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-5 py-2 bg-[#252a36] hover:bg-[#2e3444] text-slate-300 text-xs font-medium rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="px-5 py-2 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
                >
                  {editingUserId ? 'Save changes' : 'Add user'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
