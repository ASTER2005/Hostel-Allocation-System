# Vercel deployment

Vercel's project root must be the repository root (the directory containing
`index.py`, `run.py`, and `requirements.txt`). `index.py` exports the existing
Flask WSGI app through the repository launcher. Vercel's Python runtime detects
Flask from `requirements.txt` and serves the app's existing routes and assets.

## Environment variables

Configure these in Vercel Project Settings → Environment Variables:

- `DATABASE_URL` (optional): a reachable managed PostgreSQL or MySQL database.
  PostgreSQL URLs beginning `postgres://` or `postgresql://`, and MySQL URLs
  beginning `mysql://`, are normalized to their installed SQLAlchemy drivers.
  Vercel Postgres integrations may expose `POSTGRES_URL`; that is accepted when
  `DATABASE_URL` is not present.
- `SECRET_KEY` (recommended): a long random value used to sign Flask sessions.

Without `DATABASE_URL`, the app uses in-memory SQLite so it can start without
external database setup. Vercel instances are temporary, so this fallback does
not preserve data between invocations. The app creates its schema at startup
and seeds demo fixtures only when the database is empty.

## Deploy with the Vercel CLI (PowerShell)

Run these commands from the repository root:

```powershell
npm install --global vercel
vercel login
vercel link
vercel --prod
```

For persistent production data, add `DATABASE_URL` from your managed database
provider in Vercel Project Settings. Set `SECRET_KEY` there to keep sessions
valid across function instances. Preview deployments can use separate values.

To inspect runtime failures after deployment:

```powershell
vercel logs <deployment-url>
```
