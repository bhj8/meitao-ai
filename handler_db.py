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
        for _ in range(50):
            result =  await create_activation_code(db, "24", 1)
            print(result[0])

if __name__ == "__main__":
    asyncio.run(create_tables())
    asyncio.run(main())
