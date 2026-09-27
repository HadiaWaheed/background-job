# Background Job Report API

A small FastAPI backend that demonstrates how to move slow work into a background job using Inngest.

The API accepts a report request immediately with `202 Accepted`, while the slow 8-second report generation happens in the background.

It also includes:

- Background jobs with Inngest
- Report status polling
- Retry handling
- Cron jobs
- FastAPI endpoints
- Inngest local dashboard
- Git/GitHub version control

---

## Tech Stack

- Python 3.10+
- FastAPI
- Inngest
- Uvicorn
- Git & GitHub

---

## How It Works

The project follows this flow:

1. Client sends a report request.
2. API immediately returns `202 Accepted`.
3. A `report/requested` event is sent to Inngest.
4. Inngest runs the `make-report` background function.
5. The function performs an 8-second slow step.
6. The report is built in a second step.
7. The client can check the report using the status endpoint.
8. A cron function runs every minute and logs report counts.

---

## Project Structure

```text
background-job/
│
├── app.py
├── README.md
└── .gitignore
````

---

## How to Run

### 1. Start the FastAPI API

Open the first terminal:

```powershell
$env:INNGEST_DEV="1"
uvicorn app:app --reload
```

The API runs at:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

---

### 2. Start the Inngest Dev Server

Open a second terminal:

```powershell
npx.cmd inngest-cli@latest dev -u http://localhost:8000/api/inngest
```

Open the Inngest dashboard:

```text
http://localhost:8288
```

The dashboard allows you to see functions, runs, steps, retries, and cron executions.

---

## API Endpoints

| Method | Endpoint               | Description             | Expected Response |
| ------ | ---------------------- | ----------------------- | ----------------- |
| GET    | `/health`              | Check if API is running | `200`             |
| POST   | `/reports`             | Create a new report     | `202`             |
| GET    | `/reports/{report_id}` | Check report status     | `200` / `404`     |

---

## Inngest Functions

| Function      | Trigger            | Purpose                                                  |
| ------------- | ------------------ | -------------------------------------------------------- |
| `say-hello`   | `test/hello`       | Demonstrates a background function with a 5-second sleep |
| `make-report` | `report/requested` | Generates the report in the background                   |
| `heartbeat`   | `* * * * *`        | Runs every minute and counts report statuses             |

---

## Creating a Report

Send a POST request to:

```text
POST /reports
```

with:

```json
{
  "topic": "cats"
}
```

The API immediately returns:

```json
{
  "id": "REPORT_ID",
  "status": "pending"
}
```

The response status is:

```text
202 Accepted
```

The slow work is not performed inside the API request.

---

## Report Status

Use the returned ID with:

```text
GET /reports/{report_id}
```

Initially the report can be:

```json
{
  "id": "REPORT_ID",
  "topic": "cats",
  "status": "pending"
}
```

After the background job finishes:

```json
{
  "id": "REPORT_ID",
  "topic": "cats",
  "status": "done",
  "result": "Report generated for topic: cats"
}
```

An unknown report ID returns:

```text
404 Report not found
```

---

## 202 Proof

Example POST response:

```json
{
  "id": "4fb484eb-d9cd-4561-b62d-61d4f56e43d4",
  "status": "pending"
}
```

The API responds immediately with `202 Accepted`.

First poll:

```json
{
  "id": "4fb484eb-d9cd-4561-b62d-61d4f56e43d4",
  "topic": "cats",
  "status": "pending"
}
```

Later poll:

```json
{
  "id": "4fb484eb-d9cd-4561-b62d-61d4f56e43d4",
  "topic": "cats",
  "status": "done",
  "result": "Report generated for topic: cats"
}
```

This demonstrates that the request is accepted immediately while the slow work happens in the background.

---

## Stage 3 — Retries and Bad Input

When the report topic is `"fail"`, the `build-report` step raises an error:

```text
The report oven is broken!
```

The `make-report` function is configured with:

```python
retries=2
```

This results in 3 total attempts:

```text
Attempt 1 → Failed
Attempt 2 → Failed
Attempt 3 → Failed
```

The Inngest dashboard shows the retry attempts and the final failed run.

A missing topic is rejected with `400 Bad Request` instead of being retried because invalid input should be rejected at the API boundary.

---

## Stage 4 — Cron Heartbeat

The project includes a cron function called:

```text
heartbeat
```

It uses:

```text
* * * * *
```

which means it runs every minute.

The function counts:

* Pending reports
* Completed reports
* Failed reports

Example log:

```text
Heartbeat: pending=1, done=3, failed=1
```

### Cron Questions

Every day at 08:00:

```text
0 8 * * *
```

Every Sunday at 22:00:

```text
0 22 * * 0
```

---

## Background Job Steps

The `make-report` function uses two steps:

### Step 1 — Slow Work

```text
do-the-slow-work
```

It waits for 8 seconds to simulate slow work.

### Step 2 — Build Report

```text
build-report
```

It creates the report result and saves the report as `done`.

This keeps the API request fast while the slow work happens in the background.

---

## Inngest Dashboard

The Inngest Dev Server dashboard can be opened at:

```text
http://localhost:8288
```

It shows:

* `say-hello`
* `make-report`
* `heartbeat`
* Completed runs
* Failed runs
* Retry attempts
* Individual steps
* Cron executions

### Dashboard Screenshot



## Key Concepts Learned

### Background Job

Work that starts after the API request has already returned.

### 202 Accepted

Means the server accepted the request, but the work is not finished yet.

### Polling

The client checks the status endpoint again until the report becomes `done`.

### Retry

A failed background job can automatically run again.

### Cron Job

A scheduled task that runs automatically according to a schedule.

### Inngest

A tool used in this project to run background functions, retries, and scheduled functions.

---

## Git Commits

The project was developed stage by stage with meaningful Git commits:

```text
Stage 0: hello server
Stage 1: add Inngest hello function
Stage 2: 202 + background job + status endpoint
Stage 3: retries seen, bad input rejected
Stage 4: add heartbeat cron job
Stage 5: add gitignore
```

---

## Author

Built as a backend background-job assignment using Python, FastAPI, and Inngest.

````
