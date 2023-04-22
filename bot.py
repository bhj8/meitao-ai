from fastapi import FastAPI
from services.api_openai import *
from tools.mylog import logger
from app.routers.authentication import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.user import router as user_router
from app.db.database import Base, engine

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

if __name__ == "__main__":
    import uvicorn
    host = "0.0.0.0"
    port = 443
    log_info = "info"
    logger.debug("Starting server...")
    logger.debug("Host: %s" % host)
    logger.debug("Port: %s" % port)
    logger.debug("Log level: %s" % log_info)
    uvicorn.run("bot:app", host=host, port=443, log_level="info", ssl_keyfile="/etc/letsencrypt/live/www.xiao-hui.com/privkey.pem", ssl_certfile="/etc/letsencrypt/live/www.xiao-hui.com/fullchain.pem")
