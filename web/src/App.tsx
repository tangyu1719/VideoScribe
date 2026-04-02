import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { useAppStore } from '@/store/useAppStore'
import Layout from '@/components/Layout'
import VideoDownload from '@/pages/VideoDownload'
import AIChat from '@/pages/AIChat'
import KnowledgeBase from '@/pages/KnowledgeBase'
import LinkAnalyzer from '@/pages/LinkAnalyzer'
import Settings from '@/pages/Settings'
import Logs from '@/pages/Logs'

function App() {
  const { theme } = useAppStore()

  useEffect(() => {
    // 应用主题
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<VideoDownload />} />
        <Route path="video" element={<VideoDownload />} />
        <Route path="chat" element={<AIChat />} />
        <Route path="link" element={<LinkAnalyzer />} />
        <Route path="knowledge" element={<KnowledgeBase />} />
        <Route path="settings" element={<Settings />} />
        <Route path="logs" element={<Logs />} />
      </Route>
    </Routes>
  )
}

export default App
