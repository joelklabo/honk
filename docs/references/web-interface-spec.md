# Honk Web Interface Specification

**Version:** 1.0 (Future/Stretch Goal)  
**Status:** Design Spec (Not Implemented)  
**Created:** 2025-11-19

## Overview

A Next.js-based web interface for Honk CLI that consumes the same JSON APIs and result envelopes as the terminal interface. Provides a dashboard for system monitoring, command execution, and result visualization.

## Guiding Principles

From `docs/spec.md`:
> "Textual-based TUI and a Next.js site remain stretch goals but should reuse the same introspection data. Textual can render in terminal or browser, so any view must consume the same JSON envelopes/events instead of bespoke transport."

**Key Requirements:**
1. Consume existing JSON APIs (no custom backend)
2. Use introspection data for command discovery
3. Parse result envelopes for all outputs
4. Share design patterns with TUI (Textual)
5. No duplicate logic - leverage CLI as API

## Technology Stack

### Frontend
- **Framework:** Next.js 14+ (App Router)
- **Package Manager:** pnpm@9.12.0 (via corepack)
- **UI Library:** shadcn/ui (React components)
- **Styling:** Tailwind CSS
- **State Management:** React Context + SWR for data fetching
- **Icons:** Lucide React
- **Charts:** Recharts (for PTY graphs, metrics)

### Backend Integration
- **No Custom API:** Use `honk` CLI JSON output via subprocess or HTTP bridge
- **Option 1:** Python HTTP server wrapping CLI commands
- **Option 2:** Direct subprocess execution from Next.js API routes
- **Option 3:** File-based communication via tmp/ directory

## Core Features

### 1. Dashboard (Home Page)

**Purpose:** At-a-glance system health and recent activity

**Components:**
- System status cards (CPU, memory, disk, PTYs)
- Recent command executions
- Active sessions/processes
- Quick actions (Run command, View logs)

**Data Sources:**
- `honk system summary --json`
- `honk watchdog pty show --json`
- `honk doctor --json`

### 2. Command Catalog

**Purpose:** Browse and execute available commands

**Features:**
- Tree view of areas → tools → actions
- Search/filter commands
- View command help and examples
- Execute commands with form inputs
- View result envelopes

**Data Sources:**
- `honk introspect --json` (full catalog)
- `honk help-json <command>` (per-command details)

**UI Flow:**
1. Load introspection data on mount
2. Build tree structure from `areas[]`
3. Click command → Load help-json
4. Show form for options/arguments
5. Execute → Stream/display result envelope

### 3. PTY Monitor

**Purpose:** Real-time PTY usage monitoring and cleanup

**Features:**
- Current PTY usage (total, by process)
- Process list with details (PID, command, PTY count)
- Heavy users visualization (charts)
- One-click cleanup for leaks
- Auto-refresh every 5s

**Data Sources:**
- `honk watchdog pty show --json`
- `honk watchdog pty clean --plan --json` (preview)
- `honk watchdog pty clean --json` (execute)

**UI Components:**
- Line chart: PTY usage over time
- Table: Active processes with action buttons
- Cards: Summary stats (total PTYs, process count, heavy users)
- Alert: When PTYs exceed threshold

### 4. Authentication Status

**Purpose:** View and manage auth tokens

**Features:**
- GitHub auth status (scopes, expiration)
- Azure DevOps auth status
- Refresh tokens
- Login/logout flows

**Data Sources:**
- `honk auth gh status --json`
- `honk auth az status --json`
- Execute: `honk auth <provider> <action> --json`

**Security Note:** Never show raw tokens, only status/metadata

### 5. Release Dashboard

**Purpose:** Manage releases and changelog

**Features:**
- Current version info
- Commit history since last tag
- Release type recommendation (patch/minor/major)
- Preview changelog
- Execute release

**Data Sources:**
- `honk release status --json`
- `honk release preview <type> --json`
- Execute: `honk release <type> --json`

### 6. Command Execution Terminal

**Purpose:** Execute arbitrary commands and view output

**Features:**
- Command input (autocomplete from introspection)
- Option/argument form builder
- Real-time output streaming
- Result envelope viewer (JSON tree)
- Command history
- Copy result envelope

**Implementation:**
- Parse introspection for command options
- Build dynamic form
- Execute via API route
- Stream output via Server-Sent Events or WebSockets
- Parse and display result envelope

### 7. Doctor/Health Checks

**Purpose:** View system prerequisites and remediation

**Features:**
- Run all doctor packs
- View check results (pass/fail)
- Show remediation steps
- Quick-fix buttons (execute suggested commands)

**Data Sources:**
- `honk doctor --json`
- `honk doctor --plan --json`

## Architecture

### Directory Structure

```
honk-web/
├── package.json
├── pnpm-lock.yaml
├── next.config.js
├── tailwind.config.js
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx (Dashboard)
│   │   ├── commands/
│   │   │   └── page.tsx (Command Catalog)
│   │   ├── pty/
│   │   │   └── page.tsx (PTY Monitor)
│   │   ├── auth/
│   │   │   └── page.tsx (Auth Status)
│   │   ├── release/
│   │   │   └── page.tsx (Release Dashboard)
│   │   ├── terminal/
│   │   │   └── page.tsx (Command Execution)
│   │   └── api/
│   │       ├── execute/route.ts
│   │       ├── introspect/route.ts
│   │       └── status/route.ts
│   ├── components/
│   │   ├── ui/ (shadcn components)
│   │   ├── CommandTree.tsx
│   │   ├── ResultEnvelope.tsx
│   │   ├── PTYChart.tsx
│   │   └── ProcessTable.tsx
│   ├── lib/
│   │   ├── honk.ts (CLI wrapper)
│   │   ├── types.ts (TypeScript types for envelopes)
│   │   └── utils.ts
│   └── hooks/
│       ├── useIntrospection.ts
│       ├── useHonkCommand.ts
│       └── usePTYMonitor.ts
```

### API Routes

#### `/api/execute`
- **Method:** POST
- **Body:** `{command: string[], options: Record<string, any>}`
- **Action:** Execute honk command, return result envelope
- **Streaming:** Support SSE for long-running commands

#### `/api/introspect`
- **Method:** GET
- **Action:** Cache and return `honk introspect --json`
- **Cache:** 5 minutes (introspection doesn't change often)

#### `/api/help/<command>`
- **Method:** GET
- **Action:** Return `honk help-json <command>`

#### `/api/status/pty`
- **Method:** GET
- **Action:** Return `honk watchdog pty show --json`

#### `/api/status/auth`
- **Method:** GET
- **Action:** Return auth status for all providers

### CLI Wrapper (lib/honk.ts)

```typescript
export interface ResultEnvelope {
  version: string;
  command: string[];
  status: string;
  changed: boolean;
  code: string;
  summary: string;
  run_id: string;
  duration_ms: number;
  facts: Record<string, any>;
  links?: Link[];
  next?: NextStep[];
  pack_results?: PackResult[];
}

export class HonkCLI {
  async execute(
    command: string[],
    options: Record<string, any> = {}
  ): Promise<ResultEnvelope> {
    // Build command line args from options
    const args = this.buildArgs(command, options);
    
    // Execute: uv run honk ...args --json
    const result = await execAsync(`uv run honk ${args.join(' ')} --json`);
    
    // Parse and return result envelope
    return JSON.parse(result.stdout);
  }
  
  async introspect(): Promise<IntrospectionSchema> {
    const result = await this.execute(['introspect'], {json: true});
    return result.facts;
  }
}
```

## Design System

### Color Palette (Match CLI)
- **Success:** Green (#22c55e)
- **Error:** Red (#ef4444)
- **Warning:** Yellow (#eab308)
- **Info:** Blue (#3b82f6)
- **Dim/Secondary:** Gray (#6b7280)

### Typography
- **Heading:** Inter (sans-serif)
- **Body:** Inter
- **Code:** JetBrains Mono (monospace)

### Components
- Use shadcn/ui for consistency
- Match Rich terminal aesthetics
- Responsive design (mobile-first)
- Dark mode support

## Data Flow

```
User Action → Next.js Page
  ↓
API Route (Next.js)
  ↓
Execute: uv run honk <command> --json
  ↓
Parse Result Envelope
  ↓
Return JSON to Frontend
  ↓
Display in UI
```

## Security Considerations

1. **No Token Exposure:** Never display raw auth tokens
2. **Command Validation:** Whitelist allowed commands
3. **Input Sanitization:** Validate all user inputs
4. **CSRF Protection:** Use Next.js CSRF tokens
5. **Rate Limiting:** Prevent command spam
6. **Authentication:** (Future) Add web login for multi-user

## Development Setup

```bash
# From honk repo root
cd web/

# Enable corepack for pnpm
corepack enable
corepack use pnpm@9.12.0

# Install dependencies
pnpm install

# Dev server
pnpm dev

# Build
pnpm build

# Start production
pnpm start
```

## Testing Strategy

### Unit Tests
- Component rendering (Jest + React Testing Library)
- CLI wrapper logic
- Result envelope parsing

### Integration Tests
- API routes with mocked CLI
- End-to-end command execution
- Result envelope contract tests

### E2E Tests
- Full user flows (Playwright)
- Command execution → result display
- PTY monitoring workflow

## Deployment

### Option 1: Static Export
- Build static site: `pnpm build && pnpm export`
- Serve from any static host
- API routes become serverless functions

### Option 2: Self-Hosted
- Run Next.js server locally
- Access via `http://localhost:3000`
- Ideal for local development/monitoring

### Option 3: Docker
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && corepack use pnpm@9.12.0
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build
CMD ["pnpm", "start"]
```

## Future Enhancements

### Phase 2
- WebSocket support for real-time updates
- PTY daemon integration (when implemented)
- Multi-user authentication
- Command scheduling (cron-like)
- Alert notifications

### Phase 3
- Agent execution logs viewer
- Custom dashboards
- Metrics/analytics
- Export reports (PDF, CSV)
- API key management

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
1. Set up Next.js project structure
2. Implement CLI wrapper (lib/honk.ts)
3. Create API routes for core commands
4. Build basic dashboard with system status
5. Implement introspection viewer

### Phase 2: Core Features (Week 3-4)
1. Command catalog with search
2. PTY monitor with charts
3. Authentication status page
4. Release dashboard
5. Result envelope viewer

### Phase 3: Polish (Week 5-6)
1. Command execution terminal
2. Real-time updates
3. Error handling
4. Loading states
5. Documentation

### Phase 4: Testing & Deployment (Week 7-8)
1. Write tests
2. CI/CD pipeline
3. Docker setup
4. Documentation
5. Beta release

## Maintenance

- Update when CLI schema changes
- Sync with result envelope schema updates
- Test against CLI version changes
- Keep dependencies up-to-date

## References

- Main Spec: `docs/spec.md`
- Result Envelope Schema: `schemas/result.v1.json`
- Introspection Schema: `schemas/introspect.v1.json`
- CLI Source: `src/honk/cli.py`

---

**Status:** Design spec complete, ready for implementation when prioritized.
