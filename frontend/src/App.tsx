import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ErrorBoundary } from './components/ErrorBoundary'
import { Layout } from './components/Layout'
import { AuthProvider } from './context/AuthContext'
import { AdminPage } from './pages/AdminPage'
import { AuthPage } from './pages/AuthPage'
import { HomePage } from './pages/HomePage'
import { SubmitPage } from './pages/SubmitPage'

export default function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<HomePage />} />
              <Route path="submit" element={<SubmitPage />} />
              <Route path="auth" element={<AuthPage />} />
              <Route path="admin" element={<AdminPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  )
}
