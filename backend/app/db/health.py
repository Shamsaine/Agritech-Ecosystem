from sqlalchemy import text

from app.db.session import engine


async def check_database_connection() -> bool:
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT 1")
            )
            return result.scalar_one() == 1
    except Exception:
        return False