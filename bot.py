from fastapi import FastAPI, HTTPException
from services.api_openai import *
from tools.mylog import logger
from app.routers.authentication import router as auth_router
from app.routers.chatgpt import router as chat_router
from app.routers.user import router as user_router
from app.routers.chatgpt_fast import router as chatgpt_fast_router
from app.routers.chat_sessions import router as chat_sessions_router
from app.routers.orders import router as order_router
from app.db.database import Base, engine
from app.error_codes.custom_exception_handlers import custom_http_exception_handler

# 创建所有数据表
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI()

# 在启动应用程序时创建数据表
@app.on_event("startup")
async def on_startup():
    await create_tables()

# Register routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(user_router)
app.include_router(chatgpt_fast_router)
app.include_router(chat_sessions_router)
app.include_router(order_router)

# Register exception handlers
app.exception_handler(HTTPException)(custom_http_exception_handler)

if __name__ == "__main__":
    import uvicorn
    host = "0.0.0.0"
    port = 443
    log_info = "info"
    logger.debug("Starting server...")
    logger.debug("Host: %s" % host)
    logger.debug("Port: %s" % port)
    logger.debug("Log level: %s" % log_info)
    uvicorn.run("bot:app", host=host, port=3000, log_level="info")
    # uvicorn.run("bot:app", host=host, port=port, log_level="info", ssl_keyfile="/etc/letsencrypt/live/www.xiao-hui.com/privkey.pem", ssl_certfile="/etc/letsencrypt/live/www.xiao-hui.com/fullchain.pem")
