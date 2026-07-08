# API Polling

Tags: #api #execution

Use this when a job returns `queued` or `running`.
Poll `GET /v1/jobs/{job_id}` every 5 seconds until status becomes `succeeded` or `failed`.
Do not poll faster than once per second.

```bash
curl -s "$BASE_URL/v1/jobs/$JOB_ID"
```

If the API returns 429, wait 30 seconds before retrying.
