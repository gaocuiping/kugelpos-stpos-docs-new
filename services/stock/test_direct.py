import asyncio
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from app.main import app

async def main():
    with patch('kugel_common.security.verify_token', return_value={'sub': 'admin', 'tenant_id': 'T9999', 'username': 'admin', 'is_superuser': True}):
        async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
            url = '/api/v1/tenants/T9999/stores/5678/stock/snapshot/000000000000000000000000'
            headers = {'Authorization': 'Bearer test', 'X-Tenant-ID': 'T9999', 'X-User-ID': 'admin'}
            resp = await ac.get(url, headers=headers)
            print('STATUS:', resp.status_code)
            print('BODY:', resp.text)

if __name__ == '__main__':
    asyncio.run(main())
