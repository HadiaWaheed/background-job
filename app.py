from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import inngest
import inngest.fast_api
import uuid


# --------------------------------------------------
# Reports ko temporarily memory mein store karenge
# --------------------------------------------------
reports = {}

app = FastAPI()


# --------------------------------------------------
# Request body
# POST /reports mein client "topic" bhejega
# --------------------------------------------------
class ReportRequest(BaseModel):
    topic: str


# --------------------------------------------------
# Inngest client
# --------------------------------------------------
inngest_client = inngest.Inngest(
    app_id="report-api"
)


# --------------------------------------------------
# Stage 1: Hello background function
# --------------------------------------------------
@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello"),
)
async def say_hello(ctx: inngest.Context):
    await ctx.step.sleep("wait-5-seconds", 5000)

    return "Hello from the background!"


# --------------------------------------------------
# Stage 2: Make Report background function
# --------------------------------------------------
@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested"),
)
async def make_report(ctx: inngest.Context):

    # Event se report ID aur topic nikalna
    report_id = ctx.event.data["id"]
    topic = ctx.event.data["topic"]

    # Step 1:
    # Slow work ko simulate kar rahe hain
    await ctx.step.sleep(
        "do-the-slow-work",
        8000
    )

    # Step 2:
    # Report ka result build karna
    async def build_report():
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


# --------------------------------------------------
# Inngest ko FastAPI ke saath connect karna
# --------------------------------------------------
inngest.fast_api.serve(
    app,
    inngest_client,
    [
        say_hello,
        make_report
    ]
)


# --------------------------------------------------
# Stage 0: Health check
# --------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


# --------------------------------------------------
# Stage 2: Create a report
# --------------------------------------------------
@app.post("/reports", status_code=202)
async def create_report(request: ReportRequest):

    # Unique report ID
    report_id = str(uuid.uuid4())

    # Report ko initially pending save karna
    reports[report_id] = {
        "id": report_id,
        "topic": request.topic,
        "status": "pending"
    }

    # Inngest ko background job start karne ka event bhejna
    await inngest_client.send(
        inngest.Event(
            name="report/requested",
            data={
                "id": report_id,
                "topic": request.topic
            }
        )
    )

    # Immediately response
    return {
        "id": report_id,
        "status": "pending"
    }


# --------------------------------------------------
# Stage 2: Check report status
# --------------------------------------------------
@app.get("/reports/{report_id}")
def get_report(report_id: str):

    # Agar ID exist nahi karti
    if report_id not in reports:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    # Existing report return karo
    return reports[report_id]