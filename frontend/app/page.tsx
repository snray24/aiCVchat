'use client'

import ChatPanel from '@/components/ChatPanel'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-slate-800 mb-2">IITK AIML Careers Chatbot</h1>
          <p className="text-slate-600">AI-powered resume search and candidate information</p>
        </header>

        {/* Chat Panel */}
        <div className="max-w-4xl mx-auto">
          <ChatPanel />
        </div>
      </div>
    </main>
  )
}
