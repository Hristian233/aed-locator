# AED Locator

Production-oriented web application to find the nearest Automated External Defibrillator (AED) during emergencies and submit new locations for admin verification.

## Architecture

```
┌─────────────┐     HTTPS      ┌──────────────────┐     PostGIS    ┌─────────────┐
│  React SPA  │ ─────────────► │  FastAPI (async) │ ─────────────► │ PostgreSQL  │
│ Vite/Google  │               │  Clean layers    │                │  + PostGIS  │
└─────────────┘                └──────────────────┘                └─────────────┘
       │                                │
       │                                ├── JWT auth
       │                                ├── Rate-limited submissions
       │                                └── AI heuristics (image / spam / dupes)
```

| Layer | Responsibility |
|-------|----------------|
| `frontend/` | Map UI, geolocation, navigation links, submit flow, admin queue |
| `backend/app/api` | HTTP routes, auth deps, rate limits |
| `backend/app/services` | Business rules, AI helpers, file storage |
| `backend/app/repositories` | PostGIS queries (nearest, duplicates) |
| `backend/app/models` | SQLAlchemy entities |

### Key decisions

- **PostGIS** — `ST_DWithin` and KNN (`<->`) for fast nearest-AED queries at scale.
- **Verification workflow** — Public map shows only `verified` AEDs; submissions start as `pending`.
- **MVP AI** — Heuristic image/spam/duplicate checks in `AIService`; swap for Vertex AI / Cloud Vision in production without changing API contracts.
- **JWT auth** — Simple stateless tokens; Firebase Auth can replace `AuthService` later.
- **Google Maps** — Maps JavaScript API via `@vis.gl/react-google-maps`; set `VITE_GOOGLE_MAPS_API_KEY` for the frontend (and `GOOGLE_MAPS_API_KEY` on the API if you add server-side geocoding later).

## Quick start (Docker)

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| API docs | http://localhost:8080/docs |
| Web app | http://localhost:3000 |
| Postgres | `localhost:5432` |

Run migrations + seed (included in `migrate` service on first boot):

- Admin: `admin@aedlocator.local` / `adminchange1`
- Sample verified AEDs in Sydney & Melbourne

### Local development (without Docker)

**Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Start PostGIS locally, then:
export DATABASE_URL=postgresql+asyncpg://aed:aed@localhost:5432/aed_locator
alembic upgrade head
python scripts/seed.py   # run from backend/ (or use seed_sofia.sql via psql)
uvicorn app.main:app --reload --port 8080
```

**Frontend**

```bash
cd frontend
cp .env.example .env
# Add your Maps JavaScript API key to .env
npm install
npm run dev
```

Vite proxies `/api` and `/uploads` to `http://localhost:8080`.

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/aeds` | List AEDs (paginated) |
| GET | `/api/v1/aeds/nearest` | Nearest verified AEDs |
| POST | `/api/v1/aeds` | Submit AED (multipart, rate limited) |
| GET | `/api/v1/admin/aeds/pending` | Admin: pending queue |
| POST | `/api/v1/admin/aeds/{id}/verify` | Admin: approve |
| POST | `/api/v1/admin/aeds/{id}/reject` | Admin: reject |

## Environment variables

See `backend/.env.example` and `frontend/.env.example`.

Production secrets (GCP Secret Manager recommended):

- `DATABASE_URL` — Cloud SQL connection string
- `SECRET_KEY` — JWT signing key
- `ADMIN_EMAILS` — comma-separated admin bootstrap emails
- `VITE_GOOGLE_MAPS_API_KEY` — Maps JavaScript API (frontend build)
- `GOOGLE_MAPS_API_KEY` — optional server-side Maps / geocoding on the API

## GCP deployment (recommended path)

1. **Cloud SQL** — PostgreSQL 16 + PostGIS extension.
2. **Artifact Registry** — Build and push images from `backend/Dockerfile` and `frontend/Dockerfile`.
3. **Cloud Run** — Deploy API and web services; connect API to Cloud SQL via connector (see `deploy/cloud-run-api.yaml`).
4. **Secret Manager** — Mount `DATABASE_URL`, `SECRET_KEY` as secrets.
5. **Firebase Hosting** (optional) — Host static `frontend/dist` with rewrite to Cloud Run API.
6. **Cloud Storage** — Replace local `uploads/` with signed URLs for AED photos.

```bash
# Example API deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/aed-locator-api ./backend
gcloud run deploy aed-locator-api --image gcr.io/PROJECT_ID/aed-locator-api --region us-central1
```

## CI/CD

GitHub Actions workflow: `.github/workflows/ci.yml`

- Backend: migrate against PostGIS service, import app
- Frontend: `npm ci` + `npm run build`

Extend with:

- `gcloud run deploy` on `main` merge
- Integration tests with `httpx.AsyncClient`
- Container scanning (Trivy)

## Roadmap to production

- [ ] Cloud Storage + CDN for images
- [ ] Vertex AI / Cloud Vision for AED image classification
- [ ] Firebase Auth or Identity Platform
- [ ] Email notifications for verifiers
- [ ] Observability: Cloud Logging, Error Reporting, traces
- [ ] E2E tests (Playwright) for map + submit flows

## License

MIT (adjust as needed for your organization).
