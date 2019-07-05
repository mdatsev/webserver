import aiofiles
import asyncio

async def main():
    async with aiofiles.open('file', mode='rb') as f:
        data = await f.read()

asyncio.run(main())