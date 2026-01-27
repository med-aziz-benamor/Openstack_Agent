"""
Main FastAPI application for OpenStack Admin Assistant Portal.
"""
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.schemas import AnalysisResponse, HealthResponse, VersionResponse
from app.parsers.bundle_parser import BundleParser
from app.utils.hashing import compute_sha256
from app.utils.safe_extract import safe_extract_tar

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    logger.info("Starting OpenStack Admin Assistant Portal API")
    yield
    logger.info("Shutting down OpenStack Admin Assistant Portal API")


app = FastAPI(
    title="OpenStack Admin Assistant Portal",
    description="API for analyzing OpenStack diagnostic bundles",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for local development (optional, not needed with Nginx proxy)
if settings.ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8088"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        Health status response
    """
    return HealthResponse(status="ok")


@app.get("/api/version", response_model=VersionResponse)
async def get_version() -> VersionResponse:
    """
    Get API version.
    
    Returns:
        Version information
    """
    return VersionResponse(version="0.1.0")


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_bundle(bundle: UploadFile = File(...)) -> AnalysisResponse:
    """
    Upload and analyze an OpenStack diagnostic bundle.
    
    Args:
        bundle: Uploaded tar.gz file
        
    Returns:
        Analysis results including services, errors, and recommendations
        
    Raises:
        HTTPException: If file is invalid or too large
    """
    # Validate file extension
    if not bundle.filename or not bundle.filename.endswith(('.tar.gz', '.tgz')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a .tar.gz or .tgz file."
        )
    
    # Read file content
    try:
        file_content = await bundle.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")
    
    # Check file size
    file_size_mb = len(file_content) / (1024 * 1024)
    if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB"
        )
    
    logger.info(f"Analyzing bundle: {bundle.filename} ({file_size_mb:.2f}MB)")
    
    # Compute file hash
    try:
        file_hash = compute_sha256(file_content)
        logger.debug(f"File SHA256: {file_hash}")
    except Exception as e:
        logger.error(f"Failed to compute file hash: {e}")
        file_hash = "unknown"
    
    # Extract bundle safely
    try:
        extract_path = safe_extract_tar(
            file_content,
            bundle.filename or "unknown.tar.gz"
        )
        logger.info(f"Bundle extracted to: {extract_path}")
    except ValueError as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected extraction error: {e}")
        raise HTTPException(status_code=500, detail="Failed to extract bundle")
    
    # Parse bundle
    try:
        parser = BundleParser(extract_path)
        analysis_result = parser.analyze()
        
        # Add metadata
        analysis_result["metadata"]["file_hash"] = file_hash
        analysis_result["metadata"]["uploaded_filename"] = bundle.filename
        
        logger.info(f"Analysis completed for {bundle.filename}")
        return AnalysisResponse(**analysis_result)
        
    except Exception as e:
        logger.error(f"Parsing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse bundle: {str(e)}"
        )
    finally:
        # Cleanup: parser handles cleanup in its destructor
        pass


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unexpected errors.
    
    Args:
        request: The request that caused the error
        exc: The exception that was raised
        
    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
