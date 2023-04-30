# custom_exception_handlers.py
from fastapi.responses import JSONResponse
from fastapi import Request, HTTPException
from app.error_codes.error_codes import ErrorCode, ErrorMessage

async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return JSONResponse(status_code=200,content={"status": "Unauthorized", "detail": "Invalid token"})
    elif exc.status_code == ErrorCode.NOT_MEMBER:
        return JSONResponse(status_code=200,content={"status": "Success", "messages": ErrorMessage.NOT_MEMBER})
    else:
        return JSONResponse(status_code=500, content={"message": "An error occurred while processing the request."})
    
    
    
