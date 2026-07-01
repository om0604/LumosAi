# Lumos Frontend Architecture

The Lumos frontend avoids modern JavaScript frameworks (like React or Vue) or build tools (Webpack/Vite), leaning instead on native ES6 browser capabilities and vanilla CSS to provide a highly performant, zero-dependency foundation.

## Modularity

The application logic is split into distinct ES6 modules:
- `api.js`: Abstracts the `fetch()` API calls to the backend.
- `state.js`: A simple centralized state container that tracks the current uploaded documents and the active active selection.
- `helpers.js`: Pure functions for text parsing and formatting.
- `ui.js`: Imperative DOM manipulation functions (rendering documents, updating chat history, handling animations).
- `app.js`: The central orchestrator that wires up Event Listeners to UI interactions and coordinates the state/api flow.

## Design System

The visual language follows the **Lumos Design System v1.0**.
- **Tokens**: Centralized in `variables.css`. All colors, fonts, radii, and shadows reference standard tokens.
- **Typography**: Uses the editorial `Playfair Display` specifically for hero headers, and `Inter` everywhere else for supreme readability.
- **Micro-interactions**: Uses highly subtle (180ms-220ms) fade and slide transitions, actively avoiding "bouncing" animations for a mature, premium feel.
