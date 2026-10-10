import asyncio
import sys

from mcp import ClientSession
from mcp.client.sse import sse_client


async def main():
    async with sse_client('http://127.0.0.1:8100/sse') as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool('go_to_url', {'url': 'https://www.inkers.ai/'})
            print(str(result)[:2500])


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(main())
