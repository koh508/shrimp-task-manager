import os

import uvicorn
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "OK", "service": "Simple AI Chat"}


@app.post("/chat")
def chat(message: str = ""):
    return {"success": True, "response": f"Received: {message}"}


@app.get("/chat/interface")
def chat_interface():
    return {"message": "Chat interface is running."}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8011))
    uvicorn.run(app, host="0.0.0.0", port=port)
