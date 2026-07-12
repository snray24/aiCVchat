'use client'

import { useState } from 'react'
import { Filter } from 'lucide-react'

export default function FilterPanel() {
  const [filters, setFilters] = useState({
    skills: '',
    minYearsExperience: '',
    currentTitle: '',
    education: '',
    location: ''
  })

  const handleChange = (field: string, value: string) => {
    setFilters(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-5 h-5 text-primary-500" />
        <h2 className="text-xl font-semibold text-slate-800">Filters</h2>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Skills (comma-separated)
          </label>
          <input
            type="text"
            value={filters.skills}
            onChange={(e) => handleChange('skills', e.target.value)}
            placeholder="e.g., python, machine learning"
            className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Min Years Experience
          </label>
          <input
            type="number"
            value={filters.minYearsExperience}
            onChange={(e) => handleChange('minYearsExperience', e.target.value)}
            placeholder="e.g., 5"
            min="0"
            className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Job Title
          </label>
          <input
            type="text"
            value={filters.currentTitle}
            onChange={(e) => handleChange('currentTitle', e.target.value)}
            placeholder="e.g., Software Engineer"
            className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Education
          </label>
          <input
            type="text"
            value={filters.education}
            onChange={(e) => handleChange('education', e.target.value)}
            placeholder="e.g., Computer Science"
            className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Location
          </label>
          <input
            type="text"
            value={filters.location}
            onChange={(e) => handleChange('location', e.target.value)}
            placeholder="e.g., San Francisco"
            className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      <div className="mt-4 p-3 bg-slate-50 rounded-lg">
        <p className="text-xs text-slate-500">
          Filters are applied when you search or chat. Leave fields empty to ignore.
        </p>
      </div>
    </div>
  )
}
