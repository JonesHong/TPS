# TPS Frontend

This is the frontend for the Translation Proxy System (TPS).

## Tech Stack

- **Framework**: SvelteKit (Svelte 5)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Custom components inspired by shadcn-svelte

## Getting Started

### Prerequisites

- Node.js 18+ or pnpm

### Installation

```bash
cd frontend
pnpm install
```

### Development

```bash
pnpm dev
```

The development server will start at `http://localhost:5173`.

### Build

```bash
pnpm build
```

### Preview Production Build

```bash
pnpm preview
```

## Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── api/          # API client wrappers
│   │   ├── components/   # UI components
│   │   │   ├── charts/   # Chart components
│   │   │   ├── common/   # Common components (Pagination, etc.)
│   │   │   ├── dashboard/# Dashboard-specific components
│   │   │   ├── history/  # History page components
│   │   │   └── ui/       # Base UI components
│   │   └── types/        # TypeScript interfaces
│   ├── routes/
│   │   ├── +layout.svelte    # Main layout
│   │   ├── +page.svelte      # Dashboard (/)
│   │   ├── history/
│   │   │   └── +page.svelte  # History page
│   │   └── translate/
│   │       └── +page.svelte  # Translate page
│   ├── app.css           # Global styles
│   ├── app.d.ts          # Type declarations
│   └── app.html          # HTML template
├── static/               # Static assets
├── package.json
├── svelte.config.js
├── tailwind.config.js
└── vite.config.ts
```

## Pages

### Dashboard (/)

- KPI cards showing total translations, characters, cost, and cache hit rate
- Provider usage pie chart
- Daily volume bar chart

### History (/history)

- Search translations
- Filter by provider, source/target language
- Paginated table with expandable rows

### Translate (/translate)

- Real-time translation interface
- Language selection with auto-detect
- AI refinement toggle
- Copy to clipboard

## API Endpoints Used

- `GET /api/v1/stats/dashboard` - Dashboard statistics
- `GET /api/v1/translations` - Paginated translations list
- `GET /api/v1/languages` - Available languages
- `POST /api/v1/translate` - Execute translation
