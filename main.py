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

async def swap_eth_woo(woofi, amount):
    to_amount = TokenAmount(amount)
    await woofi.swap_eth_to_woo(amount=to_amount)

async def swap_eth_usdc(woofi, amount):
    to_amount = TokenAmount(amount)
    await woofi.swap_eth_to_usdc(amount=to_amount)

async def swap_usdc_eth(woofi, amount):
    to_amount = TokenAmount(amount, decimals=6)
    await woofi.swap_usdc_to_eth(amount=to_amount)

async def cross_chain(woofi, amount):
    to_amount = TokenAmount(amount)
    await woofi.eth_cross_chain_swap(amount=to_amount)

async def stake(woofi, amount):
    to_amount = TokenAmount(amount)
    await woofi.stake_woo(amount=to_amount)

async def unstake(woofi, amount):
    to_amount = TokenAmount(amount)
    await woofi.unstake_woo(amount=to_amount)

async def main():
    wallets = await load_wallets()
    amount = 0.1 # put your amount here

    tasks = []
    for wallet in wallets:
        client = Client(wallet=wallet, network=Arbitrum)
        woofi = WooFi(client=client)
        tasks.append(asyncio.create_task(swap(woofi=woofi, amount=amount_eth))) 
        # duplicate this string, if you need to do multiple operations in 1 wallet
        
        # specify the desired operation name by specifying the functions that are specified above(swap_eth_woo, etc.)..
        # ..instead of "swap" in these strings
        tasks.append(asyncio.create_task(swap(woofi=woofi, amount=amount_eth)))
        tasks.append(asyncio.create_task(swap(woofi=woofi, amount=amount_eth)))

    for completed_task in asyncio.as_completed(tasks):
        try:
            await completed_task
        except ValueError as err:
            print(f"Exception cathed: {err}")


if __name__ == "__main__":
    asyncio.run(main())