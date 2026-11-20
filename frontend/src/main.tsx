import { StrictMode, useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import '@fontsource-variable/inter'
import './styles.css'
import { App } from './App'
import { Login } from './pages/Login'
import { hasCredentials, clearCredentials, hostedDemo } from './api'

function Root() {
  const [authed, setAuthed] = useState(() => !hostedDemo || hasCredentials())

  useEffect(() => {
    if (!hostedDemo) return
    const handler = () => setAuthed(false)
    window.addEventListener('yesrole:unauthorized', handler)
    return () => window.removeEventListener('yesrole:unauthorized', handler)
  }, [])

  if (!authed) return <Login onLogin={() => setAuthed(true)} />
  return <BrowserRouter><App /></BrowserRouter>
}

createRoot(document.getElementById('root')!).render(
  <StrictMode><Root /></StrictMode>,
)
