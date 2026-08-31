from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse

class NotFoundException(Exception):
    def __init__(self, detail: str):
        self.detail = detail

class DuplicateException(Exception):
    def __init__(self, detail: str):
        self.detail = detail

class ForbiddenException(Exception):
    def __init__(self, detail: str):
        self.detail = detail

class ValidationException(Exception):
    def __init__(self, detail: str):
        self.detail = detail

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(NotFoundException)
    async def not_found_handler(request: Request, exc: NotFoundException):
        return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": exc.detail}})

    @app.exception_handler(DuplicateException)
    async def duplicate_handler(request: Request, exc: DuplicateException):
        return JSONResponse(status_code=409, content={"error": {"code": "DUPLICATE", "message": exc.detail}})

    @app.exception_handler(ForbiddenException)
    async def forbidden_handler(request: Request, exc: ForbiddenException):
        return JSONResponse(status_code=403, content={"error": {"code": "FORBIDDEN", "message": exc.detail}})

    @app.exception_handler(ValidationException)
    async def validation_handler(request: Request, exc: ValidationException):
        return JSONResponse(status_code=422, content={"error": {"code": "VALIDATION_ERROR", "message": exc.detail}})
