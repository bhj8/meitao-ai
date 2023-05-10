from app.db.database import Base, engine, get_db
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from app.db.crud import *

# 创建所有数据表
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 主函数
async def main():
    async with AsyncSession(engine) as db:
        await get_activation_code(db)
        # await delete_user(db)


async def delete_user(db):
    username = "15079857414"
    await delete_user_by_username(db, username)
    print("delete user success" + username)
    
#获取礼品码
async def get_activation_code(db):
    for _ in range(1):
        result =  await create_activation_code(db, "720", 1)
        print(result[0])

if __name__ == "__main__":
    asyncio.run(create_tables())
    asyncio.run(main())
