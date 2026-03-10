import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.enums.cart_status import CartStatus

async def main():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
        headers = {'x-api-key': 'Cb2m5jxo2kYc_D9To8zlGnLfkQAWwfwK2cZ9GPNqBsM', 'X-Tenant-ID': 'T9999'}
        terminal_id = 'T9999-5678-9'
        create_data = {'customerCode': '0001', 'staffCode': '2001', 'storeCode': '5678', 'terminalNo': 9}
        r1 = await ac.post(f'/api/v1/carts?terminal_id={terminal_id}', json=create_data, headers=headers)
        if r1.status_code != 201:
            print('Create Cart Failed:', r1.text)
            return
        cid = r1.json()['data']['cartId']
        
        add_item_data = {'itemCode': '49-01', 'quantity': 1}
        r2 = await ac.post(f'/api/v1/carts/{cid}/lineItems?terminal_id={terminal_id}', json=[add_item_data], headers=headers)
        r3 = await ac.post(f'/api/v1/carts/{cid}/subtotal?terminal_id={terminal_id}', headers=headers)
        total_amount = r3.json()['data']['totalAmount']
        
        payment1 = {
            'paymentCode': 'cash',
            'amount': total_amount * 0.3,
            'detail': str({'note': 'First payment'}),
        }
        r4 = await ac.post(f'/api/v1/carts/{cid}/payments?terminal_id={terminal_id}', json=[payment1], headers=headers)
        print('PAYMENT STATUS:', r4.status_code)
        print('PAYMENT BODY:', r4.text)

if __name__ == '__main__':
    asyncio.run(main())
