import asyncio
from src.services.worker import TaskWorker


async def main():
    worker = TaskWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
