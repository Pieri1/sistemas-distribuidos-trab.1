from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

#TUTORIAL = https://mahdijafaridev.medium.com/implementing-server-sent-events-sse-with-fastapi-real-time-updates-made-simple-6492f8bfc154

app = FastAPI()

async def event_generator():
    counter = 1
    while True:
        # Yield server-sent events formatted as ' <message>\n\n'
        yield f" Server event {counter}\n\n"
        counter += 1
        await asyncio.sleep(2)  # Simulate delay between messages

@app.get("/sse")
async def sse_endpoint():
    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=5000, reload=True)