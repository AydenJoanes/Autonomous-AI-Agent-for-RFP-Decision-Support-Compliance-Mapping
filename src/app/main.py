from fastapi import FastAPI
from src.app.api.routes import health, recommendation

app = FastAPI(title="RFP Bid Agent", version="1.0.0")

# Register routers
app.include_router(health.router)
app.include_router(recommendation.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.app.main:app", host="0.0.0.0", port=8000, reload=True)
