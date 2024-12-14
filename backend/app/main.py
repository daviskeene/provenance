from fastapi import FastAPI
from routers import sessions
from database import engine, init_db
from models import Base
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Provenance MVP")

Base.metadata.create_all(bind=engine)

app.include_router(sessions.router)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def read_root():
    return {"name": "Provenance", "version": "0.1", "status": "ok"}
