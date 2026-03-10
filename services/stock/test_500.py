import asyncio
import os
import sys

from motor.motor_asyncio import AsyncIOMotorClient
from app.services.snapshot_service import SnapshotService

async def main():
    client = AsyncIOMotorClient('mongodb://localhost:27017/?replicaSet=rs0&directConnection=true')
    db = client['db_stock_T9999']
    svc = SnapshotService(db)
    try:
        res = await svc.get_snapshot_by_id_async('000000000000000000000000')
        print('Result:', res)
    except Exception as e:
        print('Exception:', type(e), e)
    finally:
        client.close()

if __name__ == '__main__':
    asyncio.run(main())
