# Lumos Project Structure

The repository is organized into distinct domain areas:

```text
Lumos/
├── backend/                  # FastAPI Application
│   ├── routes/               # API endpoint definitions (documents, chat)
│   ├── schemas/              # Pydantic data validation models
│   ├── services/             # Core business logic (RAG pipeline)
│   ├── ingest.py             # PDF extraction and chunking script
│   ├── storage.py            # Supabase Storage helper functions
│   ├── database.py           # Supabase client instantiation
│   └── main.py               # FastAPI entry point
│
├── frontend/                 # Vanilla JS / HTML / CSS Client
│   ├── css/                  # Modular CSS architecture
│   │   ├── variables.css     # Lumos Design System tokens
│   │   ├── layout.css        # Structural grid/flex rules
│   │   ├── components.css    # Buttons, cards, chat bubbles
│   │   └── animations.css    # Keyframes and state transitions
│   │
│   ├── js/                   # Native ES6 Modules
│   │   ├── app.js            # Main orchestrator and event listeners
│   │   ├── api.js            # Fetch abstractions
│   │   ├── ui.js             # Imperative DOM rendering
│   │   ├── state.js          # Centralized data store
│   │   └── config.js         # Environment config
│   │
│   └── index.html            # Single page markup
│
└── docs/                     # Technical Documentation
    └── sql/                  # Supabase database definitions
```
