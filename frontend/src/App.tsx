import { useLayoutEffect, useState } from 'react'
import { ChartNoAxesCombined, ChevronRight, Clock3, FileStack, LayoutDashboard, Menu, Plus, Settings2, Sparkles, X } from 'lucide-react'
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { Brand, Empty, PrimaryLink } from './components'
import { Dashboard, History, Library, Settings } from './pages/Workspace'
import { NewAnalysis } from './pages/NewAnalysis'
import { Report } from './pages/Report'
import { Compare, Studio } from './pages/Studio'
import { hostedDemo } from './api'

const navigation = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/new', label: 'New Analysis', icon: Plus },
  { to: '/resumes', label: 'My Resumes', icon: FileStack },
  { to: '/studio', label: 'Optimization Studio', icon: Sparkles },
  { to: '/history', label: 'Analysis History', icon: Clock3 },
  { to: '/settings', label: 'Settings', icon: Settings2 },
]

export function App() {
  const { pathname } = useLocation()
  const [menuFor, setMenuFor] = useState<string | null>(null)
  useLayoutEffect(() => {
    if (document.scrollingElement) document.scrollingElement.scrollTop = 0
  }, [pathname])
  const open = menuFor === pathname
  const page = pathname.startsWith('/analysis/') ? 'Match Report'
    : pathname.startsWith('/compare/') ? 'Before & After'
    : navigation.find(item => item.to === '/' ? pathname === '/' : pathname.startsWith(item.to))?.label ?? 'Workspace'
  return <div className="shell">
    <a className="skip" href="#content">Skip to content</a>
    {open && <button className="scrim" aria-label="Close navigation" onClick={() => setMenuFor(null)} />}
    <aside className={'sidebar ' + (open ? 'is-open' : '')}>
      <div className="brand-row"><Brand /><button className="icon-button close-nav" aria-label="Close navigation" onClick={() => setMenuFor(null)}><X size={20} /></button></div>
      <nav aria-label="Main navigation">
        <div className="nav-label">Workspace</div>
        {navigation.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end={to === '/'} onClick={() => setMenuFor(null)}>
          <Icon size={18} /><span>{label}</span>
        </NavLink>)}
      </nav>
      <div className="sidebar-bottom">
        <div className="sidebar-info"><ChartNoAxesCombined size={19} /><div><strong>YesRole</strong><small>Align Smarter. Apply Stronger.</small></div></div>
      </div>
    </aside>
    <div className="main-shell">
      <header className="topbar">
        <button className="icon-button mobile-nav" aria-label="Open navigation" aria-expanded={open} onClick={() => setMenuFor(open ? null : pathname)}><Menu size={22} /></button>
        <div className="crumb"><Link to="/">Workspace</Link><ChevronRight size={15} /><span>{page}</span></div>
        <div className="local"><i /> {hostedDemo ? 'Private demo' : 'Local demo mode'}</div>
      </header>
      <main className="content" id="content" key={pathname}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/new" element={<NewAnalysis />} />
          <Route path="/analysis/:id" element={<Report />} />
          <Route path="/studio/:id?" element={<Studio />} />
          <Route path="/compare/:id" element={<Compare />} />
          <Route path="/resumes" element={<Library />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Empty title="Page not found" detail="Start a new analysis or return to the dashboard."><PrimaryLink /></Empty>} />
        </Routes>
      </main>
    </div>
  </div>
}
