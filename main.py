from web3 import Web3
from web3.middleware import geth_poa_middleware

from client import Client
# from client import Client
from tasks.woofi import WooFi
from config import private_key
from models import TokenAmount, Arbitrum

import time, asyncio

client = Client(private_key=private_key, network=Arbitrum)
# client.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

woofi = WooFi(client=client)
amount = TokenAmount(0.0001)

async def main():
    tasks = []
    for call in range(3):
        tasks.append(asyncio.create_task(client.check_balance_interface(
            token_address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            min_value=1
        )))
    
    results = await asyncio.gather(*tasks)
    for res in results:
        print(res)

async def get_dec():
    tasks = []
    for call in range(3):
        tasks.append(asyncio.create_task(client.get_decimals(
            contract_address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        )))
    
    results = await asyncio.gather(*tasks)
    for res in results:
        print(res)

async def swap():
    tasks = []
    for swap in range(30):
        tasks.append(asyncio.create_task(woofi.swap_eth_to_usdc(amount=amount)))
    
    return await asyncio.wait(tasks)



def main2():
    for call in range(10):
        client.check_balance_interface(
            token_address="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            min_value=1
        )

t1 = time.time()
asyncio.run(swap())
# main2()
print(time.time() - t1)