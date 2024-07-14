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
    await woofi.swap_eth_to_woo(amount=amount)

async def stake(woofi, amount):
    await woofi.stake_woo(amount=amount)

async def unstake(woofi, amount):
    await woofi.unstake_woo(amount=amount)

async def main():
    wallets = await load_wallets()
    amount_eth = TokenAmount(0.0001)
    amount_woo = TokenAmount(0.2)

    tasks = []
    # for wallet in wallets:
    #     client = Client(wallet=wallet, network=Arbitrum)
    #     woofi = WooFi(client=client)
    #     tasks.append(asyncio.create_task(swap(woofi=woofi, amount=amount_eth)))

    client = Client(wallet=wallets[1], network=Arbitrum)
    woofi = WooFi(client=client)
    tasks.append(asyncio.create_task(unstake(woofi=woofi, amount=amount_woo)))

    for completed_task in asyncio.as_completed(tasks):
        try:
            await completed_task
        except ValueError as err:
            print(f"Exception cathed: {err}")


if __name__ == "__main__":
    asyncio.run(main())