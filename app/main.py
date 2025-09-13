from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import libraries, documents, chunks, index

def create_app() -> FastAPI:
    app = FastAPI(
        title="Vector Database API",
        version="1.0",
        docs_url="/docs",
    )
    
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy", 
            "message": "Running",
            "version": "1.0"
        }
    
    # Include routers
    app.include_router(libraries.router, prefix="/v1")
    app.include_router(documents.router, prefix="/v1")
    app.include_router(chunks.router, prefix="/v1")
    app.include_router(index.router, prefix="/v1")
    
    return app

# Create the app instance
app = create_app()