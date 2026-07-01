# Lumos Deployment Guide

Lumos is designed to be fully deployable on free-tier platforms.

## Database: Supabase
1. Create a new Supabase project.
2. Enable `pgvector` in your database extensions.
3. Run the SQL schemas located in `docs/sql/` in the Supabase SQL editor to create the `documents` and `document_chunks` tables, as well as the `match_document_chunks` RPC.
4. Create a public storage bucket named `reports`.
5. Note your `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`.

## Backend: Koyeb / Render
Because the backend requires `sentence-transformers` (which installs PyTorch), serverless environments with strict size limits (like Vercel) often fail. We recommend container-based hosts like Koyeb or Render.

1. Connect your GitHub repository.
2. Set the build directory to `backend/`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`
5. Set your Environment Variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY` (must be the Service Role key for insertions)
   - `GROQ_API_KEY`

## Frontend: Vercel / Netlify
The frontend is pure Vanilla HTML/CSS/JS and can be hosted statically anywhere.

1. Connect your GitHub repository.
2. Set the build directory to `frontend/`.
3. Set the build command to empty (no build step).
4. Update `frontend/js/config.js` to point `API_BASE_URL` to your newly deployed backend URL (e.g. `https://lumos-api.onrender.com/api`).
