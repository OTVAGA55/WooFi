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

async def main():
    wallets = await load_wallets()

    client = Client(wallet=wallets[0], network=Arbitrum)

    woofi = WooFi(client=client)

    

if __name__ == "__main__":
    asyncio.run(main())