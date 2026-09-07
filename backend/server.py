import os

from dotenv import load_dotenv


load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.routes import repository, chat,search


app = FastAPI(title="Codebase RAG Debugger API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok"}

#Register your routers
app.include_router(repository.router)
app.include_router(chat.router)
app.include_router(search.router)  


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 4001))
    print(f"Starting server on port {port}...")
    uvicorn.run(
        "server:app",
       host="127.0.0.1",
        port=port,
        reload=False,
    )