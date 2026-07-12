# Resume Chatbot Frontend

Next.js frontend for the AI-powered resume search and chatbot application.

## Tech Stack

- **Next.js 14** with App Router
- **TypeScript**
- **Tailwind CSS**
- **Lucide React** (icons)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.example .env.local
```

3. Configure the API URL in `.env.local`:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Development

Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Build

Build for production:
```bash
npm run build
npm start
```

## Components

- **ChatPanel**: Interactive chat interface for asking questions about resumes
- **FilterPanel**: Search filters for skills, experience, title, education, location
- **ResultsPanel**: Displays candidate matches with selection functionality
- **RequestResumeModal**: Modal for requesting resumes via email
- **StatusBanner**: Success/error message display

## Features

- Real-time chat with AI about candidate resumes
- Semantic search with metadata filters
- Candidate shortlisting
- Email-based resume request with authorization
- Responsive design
- Loading and error states
