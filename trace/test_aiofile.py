import asyncio
from aiofile import AIOFile

async def main():
    async with AIOFile('file', 'rb') as f:
        data = await f.read(5)

asyncio.run(main())