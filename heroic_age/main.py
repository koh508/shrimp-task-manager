import os

import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "OK", "service": "HeroicAge Full MCP"}


@app.get("/docs")
def docs():
    return {"message": "HeroicAge Full MCP Docs"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)
