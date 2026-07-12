'use client'

import { useState } from 'react'
import { X, Mail, Loader2 } from 'lucide-react'

interface RequestResumeModalProps {
  resumeIds: string[]
  onSuccess: () => void
  onError: (message: string) => void
  onClose: () => void
}

export default function RequestResumeModal({
  resumeIds,
  onSuccess,
  onError,
  onClose
}: RequestResumeModalProps) {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return

    setIsLoading(true)

    try {
      const response = await fetch(`${apiBaseUrl}/api/request-resumes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          resume_ids: resumeIds
        })
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(`Request API error ${response.status}: ${text}`)
      }

      const data = await response.json()

      if (data.status === 'accepted') {
        onSuccess()
      } else {
        onError(data.message || 'Request denied')
      }
    } catch (error) {
      onError('Failed to request resumes. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-2">
            <Mail className="w-5 h-5 text-primary-500" />
            <h3 className="text-lg font-semibold text-slate-800">Request Resumes</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6">
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
              className="w-full p-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              disabled={isLoading}
            />
          </div>

          <div className="mb-4 p-3 bg-slate-50 rounded-lg">
            <p className="text-sm text-slate-600">
              <strong>{resumeIds.length}</strong> resume(s) will be sent to this email
              if it is authorized.
            </p>
          </div>

          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-xs text-amber-800">
              Resumes are only shared with authorized email addresses. Your email
              will be verified before sending.
            </p>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 py-2 px-4 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !email.trim()}
              className="flex-1 py-2 px-4 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Sending...
                </>
              ) : (
                'Request'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
