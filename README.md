# FHRI Frontend (React)

Slimmed-down repo that only includes the React frontend for the FHRI robo-advisor. It expects a backend that exposes the `/ask`, `/portfolio/*`, and related endpoints; no backend code or API keys are stored here.

## Prerequisites
- Node.js 18+ and npm
- A running backend API (e.g., FastAPI) configured with **your own** provider keys (DeepSeek/OpenAI). This project never ships or stores keys.

## Run the frontend
1. Install deps
   ```bash
   cd frontend
   npm install
   ```
2. Point to your backend (optional if you use the default `http://127.0.0.1:8000`)
   ```bash
   echo REACT_APP_API_BASE_URL=http://127.0.0.1:8000 > .env
   ```
   Change the URL to wherever your backend runs.
3. Start dev server
   ```bash
   npm start
   ```
   Opens http://localhost:3000 with hot reload. If the backend is offline, the UI will show the built-in demo fallback message.

## Test the frontend
- Run interactive tests:
  ```bash
  npm test
  ```
- Build for production:
  ```bash
  npm run build
  ```
  Outputs the optimized bundle to `frontend/build/`.

## API and keys
- Backend URL comes from `REACT_APP_API_BASE_URL` (defaults to `http://127.0.0.1:8000`). You can also edit `frontend/src/api.js` directly if you prefer.
- Supply your own provider API keys to the backend process (e.g., `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`). They are never committed to this repo.

