import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './context/AuthContext'
import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'

import { Login } from './pages/Login'
import { Dashboard } from './pages/Dashboard'
import { Datasets } from './pages/Datasets'
import { UploadData } from './pages/UploadData'
import { SemanticAnalysis } from './pages/SemanticAnalysis'
import { ClassifyText } from './pages/ClassifyText'
import { TrainModel } from './pages/TrainModel'
import { ModelEvaluation } from './pages/ModelEvaluation'
import { PredictTrends } from './pages/PredictTrends'
import { ReviewFeedback } from './pages/ReviewFeedback'
import { Reports } from './pages/Reports'
import { AdminUsers } from './pages/AdminUsers'
import { AdminModels } from './pages/AdminModels'
import { InsightGraph } from './pages/InsightGraph'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/datasets" element={<Datasets />} />
                <Route path="/reports" element={<Reports />} />

                <Route element={<ProtectedRoute roles={['analyst', 'data_scientist', 'admin']} />}>
                  <Route path="/datasets/upload" element={<UploadData />} />
                  <Route path="/analysis" element={<SemanticAnalysis />} />
                  <Route path="/classify" element={<ClassifyText />} />
                </Route>

                <Route path="/models" element={<TrainModel />} />
                <Route path="/models/evaluate" element={<ModelEvaluation />} />

                <Route element={<ProtectedRoute roles={['data_scientist', 'admin']} />}>
                  <Route path="/models/train" element={<TrainModel />} />
                </Route>

                <Route element={<ProtectedRoute roles={['analyst', 'data_scientist', 'manager', 'admin']} />}>
                  <Route path="/predict" element={<PredictTrends />} />
                </Route>

                <Route element={<ProtectedRoute roles={['reviewer', 'analyst', 'data_scientist', 'admin']} />}>
                  <Route path="/review" element={<ReviewFeedback />} />
                </Route>

                <Route element={<ProtectedRoute roles={['admin']} />}>
                  <Route path="/admin" element={<Navigate to="/admin/users" replace />} />
                  <Route path="/admin/users" element={<AdminUsers />} />
                  <Route path="/admin/models" element={<AdminModels />} />
                  <Route path="/graph" element={<InsightGraph />} />
                  <Route path="/admin/graph" element={<InsightGraph />} />
                </Route>

                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
