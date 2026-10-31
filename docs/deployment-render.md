# Render deployment

The root `render.yaml` defines two services from this repository:

- `report-navigator-api`: FastAPI in Docker, with Tesseract available for scanned PDF pages.
- `report-navigator-web`: the Vite static frontend, configured to call the API service.

Both services have automatic deploys disabled so the first deploy can be started after the current API pass is reviewed. Create a Render Blueprint from the connected repository, inspect the service settings, then deploy both services from the Render dashboard.

## Before deploying

1. Add `GROQ_API_KEY` to the API service environment if Groq should be enabled. Never put the key in `render.yaml`, source control, or frontend variables.
2. Confirm the API service's public hostname matches `https://report-navigator-api.onrender.com`. If Render assigns a different hostname, update `VITE_API_BASE_URL` on the static service and redeploy it.
3. Upload a report and run a known question through the deployed UI and `/docs` before sharing the URL with judges.

The Blueprint uses Render's Free plan for a zero-cost baseline. Free web services can sleep after 15 minutes idle and lose local files on restart or sleep. Uploaded reports and the in-memory index are therefore temporary; upload the judge's report again after a restart. Use a paid API plan with a persistent disk and add registry rehydration before relying on uploaded reports across restarts.

The judge-facing web URL is the `report-navigator-web` service URL. The API documentation is at `/docs` on the API service; the question endpoint is `POST /api/v1/questions`.
