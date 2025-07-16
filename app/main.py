from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.database import engine
from .routers import auth, users
import app.models as models

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(users.router)

@app.exception_handler(HTTPException)
async def custom_http_exception(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail if isinstance(exc.detail, str) else exc.detail.get("message", str(exc.detail))}
    )

@app.get('/')
def read_root():
    return {'message': 'Welcome to the FastAPI'}




