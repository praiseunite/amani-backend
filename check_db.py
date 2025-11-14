import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name IN ('otp_code', 'otp_expires_at')")
        )
        cols = [row[0] for row in result]
        print('OTP columns found:', cols)

if __name__ == "__main__":
    asyncio.run(check())