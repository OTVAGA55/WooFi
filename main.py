from web3 import Web3, Account
from web3.middleware import geth_poa_middleware
from pathlib import Path

from libs.client import Client
from tasks.woofi import WooFi
from data.models import TokenAmount, Arbitrum

import time, asyncio, aiofiles

async def load_wallets():
    """ Loading wallets from txt file. Returns Account object. """

    async with aiofiles.open("./data/wallets.txt", 'r') as file:
        return [Account.from_key(line.replace("\n", "")) for line in (await file.readlines())]

async def swap(woofi, amount):
    delay = 10
    await woofi.swap_eth_to_usdc(amount=amount)
    # await asyncio.sleep(delay)

async def main():
    wallets = await load_wallets()
    amount_eth = TokenAmount(0.0001)

    tasks = []
    for wallet in wallets:
        client = Client(wallet=wallet, network=Arbitrum)
        woofi = WooFi(client=client)
        tasks.append(asyncio.create_task(swap(woofi=woofi, amount=amount_eth)))

    # tasks = []
    # tasks.append(asyncio.create_task(woofi.eth_cross_chain_swap(amount=amount_eth)))

    # return await asyncio.gather(*tasks)
    for completed_task in asyncio.as_completed(tasks):
        try:
            await completed_task
        except ValueError as err:
            print(f"Exception cathed: {err}")


if __name__ == "__main__":
    asyncio.run(main())