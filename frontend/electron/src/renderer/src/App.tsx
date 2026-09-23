import { AnimatePresence, motion } from 'framer-motion'
import { useEffect } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { Toaster } from 'sonner'

import { Splash } from './components/shell/Splash'
import { TopBar } from './components/shell/TopBar'
import { Sidebar } from './components/shell/Sidebar'
import { CommandPalette } from './components/shell/CommandPalette'
import { useSplash } from './hooks/useSplash'
import * as healthChecks from './lib/api/client'
import { useHealthStore } from './stores/healthStore'

import { Home } from './screens/Home'
import { RunsList } from './screens/RunsList'
import { RunShell } from './screens/RunShell'
import { Chat } from './screens/Chat'
import { RunOverview } from './screens/run/RunOverview'
import { RunAutomation } from './screens/run/RunAutomation'
import {
  RunIntent,
  RunPlan,
  RunAgents,
} from './screens/run/RunSubTabs'
import {
  RunTimeline,
  RunTools,
  RunArtifacts,
  RunEvidence,
} from './screens/run/RunTimeline'
import {
  RunApprovals,
  RunAudit,
  RunDesktop,
} from './screens/run/RunApprovals'
import { Knowledge } from './screens/Knowledge'
import { Learning } from './screens/Learning'
import { Files } from './screens/Files'
import { Settings } from './screens/Settings'
import {
  ApplicationErrorBoundary,
  KnowledgePanelErrorBoundary,
} from './components/ui/ErrorBoundary'

function WorkbenchLayout() {
  const location = useLocation()
  return (
    <div className="flex h-full bg-[#0a0a0a] text-white overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopBar />
        <AnimatePresence mode="wait">
          <motion.main
            key={location.pathname.split('/')[1]}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.12 }}
            className="flex-1 flex flex-col min-h-0 overflow-hidden"
          >
            <Outlet />
          </motion.main>
        </AnimatePresence>
      </div>
    </div>
  )
}

// Poll health every 30s
function useHealthPoller() {
  const setHealth = useHealthStore((s) => s.setHealth)
  const setLastChecked = useHealthStore((s) => s.setLastChecked)

  useEffect(() => {
    const poll = async () => {
      const checks = [
        { key: 'overall'  as const, fn: healthChecks.getHealth          },
        { key: 'model'    as const, fn: healthChecks.getHealthModel      },
        { key: 'rag'      as const, fn: healthChecks.getHealthRag        },
        { key: 'computer' as const, fn: healthChecks.getHealthComputer   },
        { key: 'database' as const, fn: healthChecks.getHealthDatabase   },
        { key: 'browser'  as const, fn: healthChecks.getHealthBrowser    },
      ]
      for (const { key, fn } of checks) {
        fn().then((r) => setHealth(key, r)).catch(() => {})
      }
      setLastChecked(Date.now() / 1000)
    }
    poll()
    const interval = setInterval(poll, 30_000)
    return () => clearInterval(interval)
  }, [])
}

export function App() {
  const { splashDone, onSplashComplete } = useSplash()
  useHealthPoller()

  if (!splashDone) {
    return <Splash onComplete={onSplashComplete} />
  }

  return (
    <ApplicationErrorBoundary>
      <Routes>
        <Route element={<WorkbenchLayout />}>
          <Route index element={<Home />} />
          <Route path="runs" element={<RunsList />} />
          <Route path="runs/:runId" element={<RunShell />}>
            <Route index element={<Navigate to="overview" replace />} />
            <Route path="overview" element={<RunOverview />} />
            <Route path="automation" element={<RunAutomation />} />
            <Route path="intent" element={<RunIntent />} />
            <Route path="plan" element={<RunPlan />} />
            <Route path="agents" element={<RunAgents />} />
            <Route path="timeline" element={<RunTimeline />} />
            <Route path="desktop" element={<RunDesktop />} />
            <Route path="tools" element={<RunTools />} />
            <Route path="artifacts" element={<RunArtifacts />} />
            <Route path="evidence" element={<RunEvidence />} />
            <Route path="approvals" element={<RunApprovals />} />
            <Route path="audit" element={<RunAudit />} />
          </Route>
          <Route path="knowledge"
            element={
              <KnowledgePanelErrorBoundary>
                <Knowledge />
              </KnowledgePanelErrorBoundary>
            }
          />
          <Route path="chat" element={<Chat />} />
          <Route path="files" element={<Files />} />
          <Route path="learning" element={<Learning />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
      <CommandPalette />
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: 'hsl(0 0% 9%)',
            border: '1px solid hsl(0 0% 18%)',
            color: 'hsl(0 0% 85%)',
            fontSize: '12px',
          },
        }}
      />
    </ApplicationErrorBoundary>
  )
}
