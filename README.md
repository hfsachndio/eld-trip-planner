# ELD Trip Planner

A full-stack app that takes a trip's **current location, pickup location,
dropoff location, and current 70-hour/8-day cycle hours used**, then returns:

1. A **route map** (current → pickup → dropoff) with distance/duration, using
   free OpenStreetMap services (Nominatim for geocoding, OSRM for routing).
2. A list of **required stops and rests** (fuel stops every 1,000 miles,
   1-hour pickup/dropoff, 30-minute driving breaks, 10-hour rests, 34-hour
   restarts) computed from FMCSA Hours-of-Service rules.
3. One or more **ELD "Driver's Daily Log" sheets**, drawn as an SVG grid
   (Off Duty / Sleeper Berth / Driving / On Duty), one per calendar day of
   the trip — same layout as the paper FMCSA log form.

Stack: **Django + Django REST Framework** (backend, stateless HOS engine) and
**React + Vite + Leaflet** (frontend).

Assumptions (per assessment spec): property-carrying driver, 70-hr/8-day
cycle, no adverse driving conditions, fueling at least every 1,000 miles,
1 hour each for pickup and drop-off.

---

## Project layout

```
eld-app/
  backend/     Django REST API (planner/hos_engine.py = HOS/ELD logic)
  frontend/    React app (form, map, log sheets)
```

## Run locally

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # edit if needed
python manage.py runserver
```

The API will be at `http://localhost:8000/api/plan-trip/` (POST).

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env            # VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

Open `http://localhost:5173`.

### Example request body

```json
{
  "current_location": "Dallas, TX",
  "pickup_location": "Oklahoma City, OK",
  "dropoff_location": "Chicago, IL",
  "current_cycle_used_hours": 12
}
```

---

## How the HOS engine works (backend/planner/hos_engine.py)

The simulator walks the trip minute-by-minute in hour-sized "chunks" and
enforces, in priority order:

1. **70-hour/8-day cycle limit** → inserts a 34-hour restart when reached.
2. **8-hour driving / 30-minute break rule** → inserts a 30-min off-duty break.
3. **11-hour driving limit & 14-hour on-duty window** → inserts a 10-hour rest.
4. **1,000-mile fuel interval** → inserts a 30-minute on-duty fuel stop.
5. Fixed 1-hour on-duty blocks for pickup and drop-off.

The resulting timeline of events is then sliced at each midnight boundary to
produce one ELD grid per calendar day, matching the structure of the FMCSA
paper log (`Off Duty`, `Sleeper Berth`, `Driving`, `On Duty (Not Driving)`).

---

## Deployment

### Backend → Render (or Railway/Fly.io — any Python host works)

1. Push this repo to GitHub.
2. Create a new **Web Service** on [render.com](https://render.com), point it
   at the repo, root directory `backend`.
3. Build command: `pip install -r requirements.txt`
   Start command: `gunicorn eld_backend.wsgi --log-file -`
4. Add env vars from `backend/.env.example` (set `DJANGO_DEBUG=False`).
5. Deploy — note the resulting URL, e.g. `https://your-app.onrender.com`.

### Frontend → Vercel

1. Import the repo on [vercel.com](https://vercel.com), set **root directory**
   to `frontend`.
2. Framework preset: Vite.
3. Add env var `VITE_API_BASE_URL` = your Render backend URL (no trailing slash).
4. Deploy.

### CORS

The backend has `CORS_ALLOW_ALL_ORIGINS = True` for simplicity in this
assessment; lock this down to your Vercel domain for production use.

---

## Still to do before submitting the assessment

This repo contains the full app. You still need to, from your own accounts:

1. `git init`, commit, and push this to a **GitHub repo**.
2. Deploy backend + frontend (links above) and confirm the hosted version works.
3. Record a **3–5 min Loom** walking through the app and the code.
4. Submit the GitHub link, hosted link, and Loom link.
