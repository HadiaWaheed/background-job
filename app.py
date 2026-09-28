from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import inngest
import inngest.fast_api
import uuid


# --------------------------------
# Reports storage
# --------------------------------

reports = {}


# --------------------------------
# FastAPI app
# --------------------------------

app = FastAPI()


# --------------------------------
# Request model
# --------------------------------

class ReportRequest(BaseModel):
    topic: str


# --------------------------------
# Inngest client
# --------------------------------

inngest_client = inngest.Inngest(
    app_id="report-api"
)


# --------------------------------
# Stage 1: Hello background function
# --------------------------------

@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(
        event="test/hello"
    ),
)
async def say_hello(ctx: inngest.Context):

    await ctx.step.sleep(
        "wait-5-seconds",
        5000
    )

    return "Hello from the background!"


# --------------------------------
# Stage 2 + Stage 3:
# Make report background function
# --------------------------------

@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(
        event="report/requested"
    ),
    retries=2,
)
async def make_report(ctx: inngest.Context):

    # Get data from event
    report_id = ctx.event.data["id"]
    topic = ctx.event.data["topic"]

    # Step 1: Slow work
    await ctx.step.sleep(
        "do-the-slow-work",
        8000
    )

    # Step 2: Build report
    async def build_report():

        # Stage 3 failure test
        if topic == "fail":
            raise Exception(
                "The report oven is broken!"
            )

        result = f"Report generated for topic: {topic}"

        reports[report_id] = {
            "id": report_id,
            "topic": topic,
            "status": "done",
            "result": result
        }

        return result

    result = await ctx.step.run(
        "build-report",
        build_report
    )

    return result


# --------------------------------
# Stage 4: Heartbeat Cron Job
# --------------------------------

@inngest_client.create_function(
    fn_id="heartbeat",
    trigger=inngest.TriggerCron(
        cron="* * * * *"
    ),
)
async def heartbeat(ctx: inngest.Context):

    pending = 0
    done = 0
    failed = 0

    # Check all reports
    for report in reports.values():

        status = report.get("status")

        if status == "pending":
            pending += 1

        elif status == "done":
            done += 1

        elif status == "failed":
            failed += 1

    # Print counts in terminal
    print(
        f"Heartbeat: "
        f"pending={pending}, "
        f"done={done}, "
        f"failed={failed}"
    )

    return {
        "pending": pending,
        "done": done,
        "failed": failed
    }


# --------------------------------
# Connect Inngest with FastAPI
# --------------------------------

inngest.fast_api.serve(
    app,
    inngest_client,
    [
        say_hello,
        make_report,
        heartbeat
    ]
)


# --------------------------------
# Health check
# --------------------------------

@app.get("/health")
def health():

    return {
        "status": "ok"
    }


# --------------------------------
# Create Report
# --------------------------------

@app.post(
    "/reports",
    status_code=202
)
async def create_report(
    request: ReportRequest
):

    # Check empty topic
    if not request.topic.strip():

        raise HTTPException(
            status_code=400,
            detail="Topic is required"
        )

    # Create unique report ID
    report_id = str(
        uuid.uuid4()
    )

    # Save pending report
    reports[report_id] = {
        "id": report_id,
        "topic": request.topic,
        "status": "pending"
    }

    # Send event to Inngest
    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={
                "id": report_id,
                "topic": request.topic
            }
        )
    )

    # Immediately return 202
    return {
        "id": report_id,
        "status": "pending"
    }


# --------------------------------
# Get Report Status
# --------------------------------

@app.get(
    "/reports/{report_id}"
)
def get_report(
    report_id: str
):

    # Report doesn't exist
    if report_id not in reports:

        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    # Return report
    return reports[report_id]