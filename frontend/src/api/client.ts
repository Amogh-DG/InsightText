const API_BASE = '/api/v1'

export interface ApiError {
  code: string
  message: string
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('insighttext_token')
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {})
  }

  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`
  }

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  })

  if (response.status === 204) {
    return {} as T
  }

  let data
  const contentType = response.headers.get('content-type')
  if (contentType && contentType.includes('application/json')) {
    data = await response.json()
  } else {
    data = await response.text()
  }

  if (!response.ok) {
    if (data && typeof data === 'object' && data.error) {
      throw new Error(data.error.message || 'Request failed')
    }
    throw new Error(typeof data === 'string' ? data : 'Request failed')
  }

  return data as T
}

export const api = {
  auth: {
    login: (body: { email: string; password: string }) =>
      request<{ access_token: string; token_type: string; user: any }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(body)
      }),
    me: () => request<any>('/auth/me'),
    createApiKey: (label: string) =>
      request<any>('/auth/api-keys', {
        method: 'POST',
        body: JSON.stringify({ label })
      }),
    listApiKeys: () => request<any[]>('/auth/api-keys')
  },
  users: {
    list: () => request<any[]>('/users'),
    create: (body: any) =>
      request<any>('/users', {
        method: 'POST',
        body: JSON.stringify(body)
      }),
    update: (id: string, body: any) =>
      request<any>(`/users/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(body)
      }),
    delete: (id: string) =>
      request<void>(`/users/${id}`, {
        method: 'DELETE'
      })
  },
  datasets: {
    list: () => request<any[]>('/datasets'),
    get: (id: string) => request<any>(`/datasets/${id}`),
    preview: (formData: FormData) =>
      request<any>('/datasets/preview', {
        method: 'POST',
        body: formData
      }),
    getStoredPreview: (id: string, limit = 10) =>
      request<any>(`/datasets/${id}/preview?limit=${limit}`),
    upload: (formData: FormData) =>
      request<any>('/datasets/upload', {
        method: 'POST',
        body: formData
      }),
    delete: (id: string) =>
      request<void>(`/datasets/${id}`, {
        method: 'DELETE'
      })
  },
  analysis: {
    run: (body: { dataset_id: string; analysis_types: string[]; num_topics?: number }) =>
      request<any>('/analysis/run', {
        method: 'POST',
        body: JSON.stringify(body)
      }),
    text: (text: string) =>
      request<any>('/analysis/text', {
        method: 'POST',
        body: JSON.stringify({ text })
      }),
    results: (datasetId: string, skip = 0, limit = 50) =>
      request<any[]>(`/analysis/${datasetId}/results?skip=${skip}&limit=${limit}`),
    summary: (datasetId: string) =>
      request<any>(`/analysis/${datasetId}/summary`),
    topics: (datasetId: string) =>
      request<any[]>(`/analysis/${datasetId}/topics`)
  },
  models: {
    list: () => request<any[]>('/models'),
    get: (id: string) => request<any>(`/models/${id}`),
    train: (body: { dataset_id: string; algorithm: string; feature_type: string; test_split: number; name?: string }) =>
      request<any>('/models/train', {
        method: 'POST',
        body: JSON.stringify(body)
      }),
    evaluate: (id: string) =>
      request<any>(`/models/${id}/evaluate`, {
        method: 'POST'
      }),
    deploy: (id: string) =>
      request<any>(`/models/${id}/deploy`, {
        method: 'POST'
      }),
    update: (id: string, body: any) =>
      request<any>(`/models/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(body)
      }),
    delete: (id: string) =>
      request<void>(`/models/${id}`, {
        method: 'DELETE'
      })
  },
  classify: {
    run: (body: { model_id?: string; text?: string; dataset_id?: string }) =>
      request<any[]>('/classify', {
        method: 'POST',
        body: JSON.stringify(body)
      })
  },
  predict: {
    single: (body: { model_id?: string; text: string }) =>
      request<any[]>('/predict', {
        method: 'POST',
        body: JSON.stringify(body)
      }),
    batch: (body: { model_id?: string; texts: string[] }) =>
      request<any[]>('/predict/batch', {
        method: 'POST',
        body: JSON.stringify(body)
      }),
    trend: (body: { dataset_id?: string; target?: string; periods?: number; period_type?: string }) =>
      request<any>('/predict/trend', {
        method: 'POST',
        body: JSON.stringify(body)
      })
  },
  feedback: {
    listPredictions: (lowConfidenceOnly = false) =>
      request<any[]>(`/predictions?low_confidence_only=${lowConfidenceOnly}`),
    submit: (body: { prediction_id: string; corrected_label: string; comment?: string; status?: string }) =>
      request<any>('/feedback', {
        method: 'POST',
        body: JSON.stringify(body)
      }),
    list: () => request<any[]>('/feedback')
  },
  reports: {
    summary: () => request<any>('/reports/summary'),
    exportUrl: (format: 'csv' | 'html', datasetId?: string) =>
      `${API_BASE}/reports/export?format=${format}${datasetId ? `&dataset_id=${datasetId}` : ''}`
  },
  settings: {
    get: () => request<any>('/settings'),
    update: (body: { confidence_threshold?: number; intent_labels?: string[] }) =>
      request<any>('/settings', {
        method: 'PATCH',
        body: JSON.stringify(body)
      })
  }
}
