'use client'

import { X, CheckCircle, AlertCircle } from 'lucide-react'

interface StatusBannerProps {
  type: 'success' | 'error'
  message: string
  onClose: () => void
}

export default function StatusBanner({ type, message, onClose }: StatusBannerProps) {
  const bgColor = type === 'success' ? 'bg-green-50' : 'bg-red-50'
  const borderColor = type === 'success' ? 'border-green-200' : 'border-red-200'
  const textColor = type === 'success' ? 'text-green-800' : 'text-red-800'
  const Icon = type === 'success' ? CheckCircle : AlertCircle

  return (
    <div className={`mb-4 p-4 border ${borderColor} ${bgColor} ${textColor} rounded-lg flex items-center justify-between`}>
      <div className="flex items-center gap-2">
        <Icon className="w-5 h-5" />
        <p className="text-sm">{message}</p>
      </div>
      <button
        onClick={onClose}
        className="hover:opacity-70 transition-opacity"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}
