'use client'

import { useState } from 'react'
import { Users, Mail, Check } from 'lucide-react'
import { authHeaders } from '../lib/embedAuth'

interface CandidateMatch {
  resume_id: string
  full_name: string
  current_title: string | null
  years_experience: number | null
  top_skills: string[]
  short_match_reason: string
}

interface ResultsPanelProps {
  selectedResumeIds: string[]
  onSelectResume: (id: string) => void
  onRequestResumes: () => void
}

export default function ResultsPanel({ 
  selectedResumeIds, 
  onSelectResume, 
  onRequestResumes 
}: ResultsPanelProps) {
  const [matches, setMatches] = useState<CandidateMatch[]>([])
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000'

  const handleSearch = async () => {
    try {
      const headers = await authHeaders(apiBaseUrl)
      const response = await fetch(`${apiBaseUrl}/api/search`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          query: 'candidates',
          filters: {},
          top_k: 8
        })
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(`Search API error ${response.status}: ${text}`)
      }

      const data = await response.json()
      setMatches(data.matches || [])
    } catch (error) {
      console.error('Search error:', error)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 h-[600px] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-primary-500" />
          <h2 className="text-xl font-semibold text-slate-800">Results</h2>
        </div>
        <button
          onClick={handleSearch}
          className="px-3 py-1 text-sm bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition-colors"
        >
          Refresh
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 mb-4">
        {matches.length === 0 ? (
          <div className="text-center text-slate-400 py-8">
            <Users className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No candidates found</p>
            <p className="text-sm mt-1">Use chat to search for candidates</p>
          </div>
        ) : (
          matches.map((match) => (
            <div
              key={match.resume_id}
              className={`p-4 border rounded-lg cursor-pointer transition-all ${
                selectedResumeIds.includes(match.resume_id)
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-slate-200 hover:border-slate-300'
              }`}
              onClick={() => onSelectResume(match.resume_id)}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold text-slate-800">{match.full_name}</h3>
                  <p className="text-sm text-slate-600">{match.current_title || 'No title'}</p>
                </div>
                {selectedResumeIds.includes(match.resume_id) && (
                  <Check className="w-5 h-5 text-primary-500" />
                )}
              </div>

              {match.years_experience !== null && (
                <p className="text-xs text-slate-500 mb-2">
                  {match.years_experience} years experience
                </p>
              )}

              {match.top_skills.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {match.top_skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 text-xs bg-slate-100 text-slate-700 rounded"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              )}

              <p className="text-xs text-slate-500">{match.short_match_reason}</p>
            </div>
          ))
        )}
      </div>

      <button
        onClick={onRequestResumes}
        disabled={selectedResumeIds.length === 0}
        className="w-full py-3 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
      >
        <Mail className="w-4 h-4" />
        Request Selected Resumes ({selectedResumeIds.length})
      </button>

      <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
        <p className="text-xs text-amber-800">
          <strong>Note:</strong> Resumes are only sent to authorized email addresses.
          You cannot view or download resumes directly.
        </p>
      </div>
    </div>
  )
}
