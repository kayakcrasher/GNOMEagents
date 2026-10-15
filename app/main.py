from fastapi import FastAPI

app = FastAPI(
    title="GNOME Agents",
    description="Small helpers. Big business.",
    version="0.1.0",
)


@app.get("/")
def home():
    return {
        "name": "GNOME Agents",
        "agent": "Leadkeeper",
        "status": "awake",
    }


@app.get("/health")
def health():
    return {"status": "green"}
