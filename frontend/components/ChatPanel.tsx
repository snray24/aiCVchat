'use client'

import { useState } from 'react'
import { Send, Loader2, RefreshCw, MapPin, Briefcase, GraduationCap } from 'lucide-react'
import RequestResumeModal from './RequestResumeModal'
import { authHeaders } from '../lib/embedAuth'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ResumeMatch {
  resume_id: string
  full_name: string
  current_title: string | null
  years_experience: number
  top_skills: string[]
  short_match_reason: string
}

type ConversationState = 'welcome' | 'awaiting_location' | 'awaiting_skill' | 'awaiting_job_title' | 'free_chat'

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: 'Hello, I am your AI guide to the IIT Kanpur AIML careers portal. You can select from a sequence of questions starting with Location, Skill or Job Title, or simply ask whatever you want to know about the candidates.'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationState, setConversationState] = useState<ConversationState>('welcome')
  const [currentMatches, setCurrentMatches] = useState<string[]>([])
  const [showRequestModal, setShowRequestModal] = useState(false)
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'

  // Detect if user is asking to send/request resumes
  const isRequestingResumes = (message: string): boolean => {
    const lowerMsg = message.toLowerCase()
    return /\b(send|share|request|mail|email|forward|transmit|provide).*\b(resume|resumes|cv|profile|document)\b/.test(lowerMsg) ||
           /\b(send|share|request|mail|email|forward|transmit|provide).*\b(their|me|them|us)\b/.test(lowerMsg)
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: 'user', content: input }
    const userQuery = input
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const headers = await authHeaders(apiBaseUrl)
      const response = await fetch(`${apiBaseUrl}/api/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          message: userQuery,
          filters: {},
          history: messages
        }),
        signal: AbortSignal.timeout(300000) // 5 minute timeout for LLM inference via ngrok
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(`Chat API error ${response.status}: ${text}`)
      }

      const data = await response.json()
      
      // Display the backend response
      const assistantMessage: Message = { role: 'assistant', content: data.answer }
      setMessages(prev => [...prev, assistantMessage])
      
      // If backend indicates email is required and we have matches, show modal
      if (data.email_required && data.matches && data.matches.length > 0 && 
          data.answer.toLowerCase().includes('email')) {
        setCurrentMatches(data.matches.map((m: any) => m.resume_id))
        setShowRequestModal(true)
      }
      
      setConversationState('free_chat')
    } catch (error) {
      console.error('Chat error:', error)
      let errorMessage = 'Sorry, I encountered an error. Please try again.'
      
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          errorMessage = 'Request timed out. The model is taking longer than expected. Please try again.'
        } else if (error.message.includes('Failed to fetch')) {
          errorMessage = 'Unable to connect to the server. Please check if the backend is running.'
        } else {
          errorMessage = `Error: ${error.message}`
        }
      }
      
      const errorResponse: Message = { 
        role: 'assistant', 
        content: errorMessage
      }
      setMessages(prev => [...prev, errorResponse])
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickOption = (option: string) => {
    setInput(option)
    if (option === 'Location') {
      setConversationState('awaiting_location')
    } else if (option === 'Skill') {
      setConversationState('awaiting_skill')
    } else if (option === 'Job Title') {
      setConversationState('awaiting_job_title')
    }
  }

  const handleReset = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Hello, I am your AI guide to the IIT Kanpur AIML careers portal. You can select from a sequence of questions starting with Location, Skill or Job Title, or simply ask whatever you want to know about the candidates.'
      }
    ])
    setConversationState('welcome')
    setInput('')
    setCurrentMatches([])
    setShowRequestModal(false)
  }

  const handleResumeRequestSuccess = () => {
    setShowRequestModal(false)
    setCurrentMatches([])
    // Don't add any message to chat - just close modal
  }

  const handleResumeRequestError = (message: string) => {
    setShowRequestModal(false)
    setCurrentMatches([])
    // Don't add any message to chat - just close modal
  }

  const handleResumeRequestClose = () => {
    setShowRequestModal(false)
    setCurrentMatches([])
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 h-[600px] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-slate-800">Chat</h2>
        <button
          onClick={handleReset}
          className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
          title="Reset conversation"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto space-y-4 mb-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`p-3 rounded-lg ${
              msg.role === 'user' 
                ? 'bg-primary-500 text-white ml-8' 
                : 'bg-slate-100 text-slate-800 mr-8'
            }`}
          >
            <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex items-center justify-center py-4">
            <Loader2 className="animate-spin text-primary-500" />
          </div>
        )}
      </div>

      {/* Quick Options */}
      {conversationState === 'welcome' && (
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => handleQuickOption('Location')}
            className="flex-1 flex items-center justify-center gap-2 p-3 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors text-slate-700"
          >
            <MapPin className="w-4 h-4" />
            <span className="text-sm">Location</span>
          </button>
          <button
            onClick={() => handleQuickOption('Skill')}
            className="flex-1 flex items-center justify-center gap-2 p-3 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors text-slate-700"
          >
            <GraduationCap className="w-4 h-4" />
            <span className="text-sm">Skill</span>
          </button>
          <button
            onClick={() => handleQuickOption('Job Title')}
            className="flex-1 flex items-center justify-center gap-2 p-3 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors text-slate-700"
          >
            <Briefcase className="w-4 h-4" />
            <span className="text-sm">Job Title</span>
          </button>
        </div>
      )}

      {/* Input Area */}
      <div className="flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            conversationState === 'awaiting_location' ? 'Enter a location...' :
            conversationState === 'awaiting_skill' ? 'Enter a skill...' :
            conversationState === 'awaiting_job_title' ? 'Enter a job title...' :
            'Type your question...'
          }
          className="flex-1 p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
          rows={2}
          disabled={isLoading}
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Send className="w-5 h-5" />
        </button>
      </div>

      {/* Request Resume Modal */}
      {showRequestModal && (
        <RequestResumeModal
          resumeIds={currentMatches}
          onSuccess={handleResumeRequestSuccess}
          onError={handleResumeRequestError}
          onClose={handleResumeRequestClose}
        />
      )}
    </div>
  )
}
