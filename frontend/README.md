# HDIS Frontend (Private Beta UI Shell)

## Setup
1. Copy env file:
   - `cp .env.example .env`
2. Install dependencies:
   - `npm install`
3. Start dev server:
   - `npm run dev`

## Notes
- UI is tenant-authenticated via Supabase session token.
- Backend API calls use bearer token and RFC9457 error display.
- Artifact gating order is enforced in UI and backend: Intent -> Risk -> Interview.
