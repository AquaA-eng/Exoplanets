# NASA Exoplanet Assistant API

Wraps validated SQL queries against a normalized NASA Exoplanet Archive
database (stars, discovery_methods, exoplanets) as live API endpoints.

## Setup

1. Drop your downloaded `nasa_exoplanets.db` file into this folder, at the
   same level as `requirements.txt` (not inside `api/`).
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run locally:
   ```
   uvicorn api.index:app --reload
   ```
4. Open `http://127.0.0.1:8000` in a browser — you should see the endpoint
   list. Try `http://127.0.0.1:8000/planets/smallest` to confirm it matches
   what you already validated in Colab (radius 0.3098).

## Endpoints

- `/planets/closest-habitable` — planets within a distance and size range
- `/planets/smallest` / `/planets/largest`
- `/planets/search` — flexible filters: max_distance, min_radius, max_radius, method
- `/stats/summary` — totals, year range, rocky vs gas giant counts
- `/stats/by-method` — planet count and average size per discovery method
- `/stars/most-planets` — stars hosting the most confirmed planets

## Deploy to Vercel

1. Push this folder to a new GitHub repository.
2. Go to vercel.com, import the repository.
3. Vercel will detect `vercel.json` and deploy automatically.
4. Your live API URL will look like `https://your-repo-name.vercel.app`.
