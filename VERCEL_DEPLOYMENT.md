# Vercel deployment

Vercel's project root must be the repository root (the directory containing
`index.py`, `run.py`, and `requirements.txt`). `index.py` exports the existing
Flask WSGI app through the repository launcher. Vercel's Python runtime detects
Flask from `requirements.txt` and serves the app's existing routes and assets.

## Environment variables

Configure these in Vercel Project Settings → Environment Variables:

- `DATABASE_URL` (required): a reachable managed PostgreSQL or MySQL database.
  PostgreSQL URLs beginning `postgres://` or `postgresql://`, and MySQL URLs
  beginning `mysql://`, are normalized to their installed SQLAlchemy drivers.
  Vercel Postgres integrations may expose `POSTGRES_URL`; that is accepted when
  `DATABASE_URL` is not present.
- `SECRET_KEY` (required): a long random value used to sign Flask sessions.

Do not use SQLite for production persistence on Vercel. Serverless filesystem
and process memory are temporary. The app creates its schema at startup and
seeds demo fixtures only when the database is empty.

## Deploy with the Vercel CLI (PowerShell)

Run these commands from the repository root:

```powershell
npm install --global vercel
vercel login
vercel link
vercel env add DATABASE_URL production
vercel env add SECRET_KEY production
vercel --prod
```

At each `vercel env add` prompt, paste the matching value from your managed
database provider or secret generator. To deploy preview branches, add the same
variables for the `preview` environment before running `vercel`.

To inspect runtime failures after deployment:

```powershell
vercel logs <deployment-url>
```
