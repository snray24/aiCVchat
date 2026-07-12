'use client'

import ChatPanel from '@/components/ChatPanel'
import FilterPanel from '@/components/FilterPanel'
import ResultsPanel from '@/components/ResultsPanel'
import RequestResumeModal from '@/components/RequestResumeModal'
import StatusBanner from '@/components/StatusBanner'
import { useState } from 'react'

export default function Home() {
  const [selectedResumeIds, setSelectedResumeIds] = useState<string[]>([])
  const [showRequestModal, setShowRequestModal] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const handleSelectResume = (resumeId: string) => {
    setSelectedResumeIds(prev => 
      prev.includes(resumeId) 
        ? prev.filter(id => id !== resumeId)
        : [...prev, resumeId]
    )
  }

  const handleRequestResumes = () => {
    if (selectedResumeIds.length === 0) {
      setStatusMessage({ type: 'error', message: 'Please select at least one resume' })
      return
    }
    setShowRequestModal(true)
  }

  const handleRequestSuccess = () => {
    setShowRequestModal(false)
    setSelectedResumeIds([])
    setStatusMessage({ type: 'success', message: 'Resumes will be sent to your email shortly' })
  }

  const handleRequestError = (message: string) => {
    setShowRequestModal(false)
    setStatusMessage({ type: 'error', message })
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-slate-800 mb-2">Resume Chatbot</h1>
          <p className="text-slate-600">Search and chat with AI about candidate resumes</p>
        </header>

        {/* Status Banner */}
        {statusMessage && (
          <StatusBanner
            type={statusMessage.type}
            message={statusMessage.message}
            onClose={() => setStatusMessage(null)}
          />
        )}

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel: Filters */}
          <div className="lg:col-span-1">
            <FilterPanel />
          </div>

          {/* Center Panel: Chat */}
          <div className="lg:col-span-1">
            <ChatPanel />
          </div>

          {/* Right Panel: Results */}
          <div className="lg:col-span-1">
            <ResultsPanel
              selectedResumeIds={selectedResumeIds}
              onSelectResume={handleSelectResume}
              onRequestResumes={handleRequestResumes}
            />
          </div>
        </div>

        {/* Request Modal */}
        {showRequestModal && (
          <RequestResumeModal
            resumeIds={selectedResumeIds}
            onSuccess={handleRequestSuccess}
            onError={handleRequestError}
            onClose={() => setShowRequestModal(false)}
          />
        )}
      </div>
    </main>
  )
}
