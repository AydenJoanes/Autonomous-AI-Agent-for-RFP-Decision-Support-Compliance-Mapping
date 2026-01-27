from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from src.app.api.routes.health import router as health_router
from src.app.api.routes.recommendation import router as recommendation_router
from src.app.api.routes.outcomes import router as outcome_router

app = FastAPI(title="RFP Bid Agent API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health_router, prefix="/api/v1", tags=["Health"])
app.include_router(recommendation_router, prefix="/api/v1/recommendation", tags=["Recommendation"])
app.include_router(outcome_router, prefix="/api/v1/outcomes", tags=["Outcomes"])

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def root():
    return FileResponse('frontend/index.html')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)
