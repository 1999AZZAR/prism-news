# PRISM News

PRISM News is a containerized news aggregator with a Python backend, Redis cache/storage, and a Swiss-archival frontend.

## Current implementation

- Backend: `server.py` (Flask API + feed ingestion)
- Frontend: `index.html` + `app.js` (vanilla JS)
- Data store: Redis (`prism-redis`)
- App container: `prism-app`
- Default app port: `5051`
- API route: `/api/news?category=<category>`

## Interface notes

- Uses a Swiss-archival layout (structured grid, restrained palette, metadata-first typography)
- Each story card includes a deterministic generated SVG specimen based on article metadata
- Card action label is `READ_MORE`

## Repository layout

- `server.py`: API service and feed retrieval logic
- `index.html`: page shell, typography, and archival layout styles
- `app.js`: category loading, card rendering, SVG specimen generation
- `requirements.txt`: Python dependencies
- `Dockerfile`: app image definition
- `docker-compose.yml`: app + Redis services

## Run locally with Docker

From the project directory:

```bash
docker compose up -d --build
```

Open:

- `http://localhost:5051`

Stop services:

```bash
docker compose down
```

Note: `docker compose down` does not remove named volumes unless `-v` is provided.

## Run without Docker

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Then open `http://localhost:5051`.

## Rebuild app only (keep Redis data)

If you are using a fixed Compose project name:

```bash
COMPOSE_PROJECT_NAME=micro-news docker compose up -d --build app
```

This rebuilds and replaces the app container without deleting the Redis volume.