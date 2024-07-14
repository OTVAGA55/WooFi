from web3 import Web3
from typing import Optional
import time, math, random, requests, asyncio, aiohttp

from libs.client import Client
from libs.utils import read_json
from data.config import WOOFI_ABI, ONEINCH_ABI, WOOFI_CCS_ABI, STARGATE_ROUTER_ABI, WOOFI_STAKE
from data.models import TokenAmount, Polygon, Arbitrum

class WooFi:
    eth_address = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
    usdc_address = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
    usdc_bridged_address = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"
    woo_address = "0xcAFcD85D8ca7Ad1e1C6F82F651fA15E33AEfD07b"

    oneinch_router = "0x1111111254EEB25477B68fb85Ed929f73A960582"
    stargate_router = "0x53Bf833A5d6c4ddA888F69c22C88C9f356a41614"

    router_abi = read_json(WOOFI_ABI)
    router_address = Web3.to_checksum_address("0x4c4AF8DBc524681930a27b2F1Af5bcC8062E6fB7")

    cross_chain_abi = read_json(WOOFI_CCS_ABI)
    cross_chain_router = Web3.to_checksum_address("0xCa10E8825FA9F1dB0651Cd48A9097997DBf7615d")

    stake_abi = read_json(WOOFI_STAKE)
    stake_address = Web3.to_checksum_address("0x2CFa72E7f58dc82B990529450Ffa83791db7d8e2")
    
    def __init__(self, client: Client):
        self.client = client

    def oneinch_data(self, decoded_pool: int, amount, min_to_amount):

        oneinch_contract = self.client.w3.eth.contract(
            address=WooFi.oneinch_router,
            abi=read_json(ONEINCH_ABI)
        )

        return oneinch_contract.encodeABI(
            'uniswapV3Swap',
            args=(
                amount.Wei,
                min_to_amount.Wei,
                [decoded_pool] # decoded pools from uniswapV3Swap
            )

        )

    # async def get_eth_price(self):
    #     return await asyncio.gather(
    #         asyncio.create_task(self.client.get_eth_price(token='ETH'))
    #     )

    async def get_oneinch_swap_data(
        self,
        network: str,
        from_token: str,
        to_token: str,
        from_amount: str,
        from_address: str,
        slippage: float
    ):
        url = f"https://fi-api.woo.org/v1/1inch_swap?network={network.name}&from_token={Web3.to_checksum_address(from_token)}&to_token={Web3.to_checksum_address(to_token)}&from_amount={from_amount.Wei}&from_address={Web3.to_checksum_address(from_address)}&slippage={slippage}"
        
        print(f"{self.client.address} | Receiving tx_info from fi-api.woo.org...")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    print(f"{self.client.address} | Received tx_info from fi-api.woo.org!")
                    tx_info = await resp.json()
                    return tx_info
                else:
                    print(f"{self.client.address} | [ERROR] Receiving tx_info from fi-api.woo.org...")
                    return False
                    

    async def swap_eth_to_usdc(self, amount: TokenAmount, slippage: float = 1):
        woofi_contract = self.client.w3.eth.contract(
            address=WooFi.router_address,
            abi=WooFi.router_abi
        )

        min_to_amount = TokenAmount(
            amount=(await self.client.get_eth_price()) * float(amount.Ether) * (1 - slippage / 100),
            decimals=6,
            wei=False
        )

        oneinch_data = self.oneinch_data(
            decoded_pool=28948022309329048855892746252806944035729668322079832629733701779868696598879,
            amount=amount,
            min_to_amount=min_to_amount
        )
        await asyncio.sleep(random.random() * 5)
        tx = await self.client.send_transaction(
            to=WooFi.router_address,
            data=woofi_contract.encodeABI(
                'externalSwap',
                args=(
                    WooFi.oneinch_router,
                    WooFi.oneinch_router,
                    WooFi.eth_address,
                    WooFi.usdc_address,
                    amount.Wei,
                    min_to_amount.Wei,
                    self.client.address,
                    oneinch_data + "31eb0e2e",
                )
            ),
            value=amount.Wei
        )
        receipt = await self.client.verif_tx(tx_hash=tx)

        return receipt
   
    async def swap_usdc_to_eth(self, amount: Optional[TokenAmount] = None, slippage: float = 1):
        if not amount:
            amount = await self.client.balance_of(contract_address=WooFi.usdc_address)

        res = await self.client.approve_interface(
            token_address=WooFi.usdc_address,
            spender=WooFi.router_address,
            amount=amount
        )
        if not res:
            return False
        await asyncio.sleep(2)

        contract = self.client.w3.eth.contract(
            address=WooFi.router_address,
            abi=WooFi.router_abi
        )

        min_to_amount = TokenAmount(
            amount=float(amount.Ether) / (await self.client.get_eth_price()) * (1 - slippage / 100)
        )

        oneinch_data = self.oneinch_data(
            decoded_pool=72370055773322622139731865631563670481975680783846483835954648774800659048656,
            amount=amount,
            min_to_amount=min_to_amount
        )

        print(f"{self.client.address} | [START] Sending USDC to ETH")
        tx = await self.client.send_transaction(
            to=WooFi.router_address,
            data=contract.encodeABI(
                'externalSwap',
                args=(
                    WooFi.oneinch_router,
                    WooFi.oneinch_router,
                    WooFi.usdc_address,
                    WooFi.eth_address,
                    amount.Wei,
                    min_to_amount.Wei,
                    self.client.address,
                    oneinch_data + "31eb0e2e",
                )
            )
        )
        receipt = await self.client.verif_tx(tx_hash=tx)

        return receipt

    async def eth_cross_chain_swap(self, amount: TokenAmount, slippage: float = 1):
        print(f"{self.client.address} | [START] Requesting tx_info from fi-api.woo.org...")

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://fi-api.woo.org/v3/cross_chain_swap?src_network=arbitrum&dst_network=polygon&src_token=0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee&dst_token=0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619&src_amount={amount.Wei}&slippage=1&extra_fee_rate=0") as resp:
                if resp.status == 200:
                    print(f"{self.client.address} | [END] TX_Info was received!")
                tx_info = await resp.json()

        contract = self.client.w3.eth.contract(
            address=WooFi.cross_chain_router,
            abi=WooFi.cross_chain_abi
        )

        min_bridge_amount = TokenAmount(
            amount=(await self.client.get_eth_price()) * float(amount.Ether) * (1 - slippage / 100),
            decimals=6,
            wei=False
        )
        ref_id = int(str(math.floor(1e4 + 9e4 * random.random())) + str(int(time.time() * 1000)))
        
        dst_chain_id = tx_info["data"]["dst_infos"]["chain_id"] # layerzero chain_id, not etherium
        dst_gas_for_call = tx_info["data"]["dst_infos"]["dst_gas_for_call"]
        dst_to_token = tx_info["data"]["dst_infos"]["to_token"]
        dst_bridged_token = tx_info["data"]["dst_infos"]["bridged_token"]
        dst_min_to_amount = TokenAmount(
            amount=int(tx_info["data"]["dst_infos"]["min_to_amount"]),
            wei=True
        )
        dst_airdrop_native_amount = 0

        dst_oneinch_data = tx_info["data"]["dst_1inch"]["data"]
        src_oneinch_data = self.oneinch_data(
            decoded_pool=1320661638825569346823283496668810617674138398049,
            amount=amount,
            min_to_amount=min_bridge_amount
        )
        src_infos = (
            WooFi.eth_address,
            WooFi.usdc_bridged_address,
            amount.Wei,
            min_bridge_amount.Wei
        )
        dst_infos = (
            dst_chain_id,
            dst_to_token,
            dst_bridged_token,
            dst_min_to_amount.Wei,
            dst_airdrop_native_amount,
            dst_gas_for_call
        )
        src_1inch = (WooFi.oneinch_router, src_oneinch_data)
        dst_1inch = (WooFi.oneinch_router, dst_oneinch_data)

        quote_layerzero_fee = TokenAmount(
            amount=(await contract.functions.quoteLayerZeroFee(ref_id, self.client.address, dst_infos, dst_1inch).call())[0],
            wei=True
        )

        # quote_layerzero_fee = TokenAmount(
        #     amount=191214017285876,
        #     wei=True
        # )

        tx = await self.client.send_transaction(
            to=WooFi.cross_chain_router,
            data=contract.encodeABI(
                'crossSwap',
                args=(
                    ref_id,
                    self.client.address,
                    src_infos,
                    dst_infos,
                    src_1inch,
                    dst_1inch
                )
            ),
            value=amount.Wei + quote_layerzero_fee.Wei
        )
        receipt = await self.client.verif_tx(tx_hash=tx)

        return receipt

    async def swap_eth_to_woo(self, amount: TokenAmount, slippage: float = 1):
        woofi_contract = self.client.w3.eth.contract(
            address=WooFi.router_address,
            abi=WooFi.router_abi
        )
        swap_data = await self.get_oneinch_swap_data(
            network=Arbitrum,
            from_token=WooFi.eth_address,
            to_token=WooFi.woo_address,
            from_amount=amount,
            from_address=WooFi.router_address,
            slippage=slippage
        )

        min_to_amount = int(swap_data['toAmount'])

        oneinch_data = swap_data['tx']['data']
        
        tx = await self.client.send_transaction(
            to=WooFi.router_address,
            data=woofi_contract.encodeABI(
                'externalSwap',
                args=(
                    WooFi.oneinch_router,
                    WooFi.oneinch_router,
                    WooFi.eth_address,
                    WooFi.woo_address,
                    amount.Wei,
                    min_to_amount,
                    self.client.address,
                    oneinch_data,
                )
            ),
            value=amount.Wei
        )
        receipt = await self.client.verif_tx(tx_hash=tx)

        await asyncio.sleep(random.random() * 5)

        return receipt

    async def stake_woo(self, amount: Optional[TokenAmount] = None, slippage: float = 1):
        if not amount:
            amount = await self.client.balance_of(contract_address=WooFi.usdc_address)

        res = await self.client.approve_interface(
            token_address=WooFi.woo_address,
            spender=WooFi.stake_address,
            amount=amount
        )
        if not res:
            return False

        await asyncio.sleep(2)

        contract = self.client.w3.eth.contract(
            address=WooFi.stake_address,
            abi=WooFi.stake_abi
        )

        print(f"{self.client.address} | Staking WOO...")
        tx = await self.client.send_transaction(
            to=WooFi.stake_address,
            data=contract.encodeABI(
                'stake',
                args=(
                    amount.Wei,
                )
            )
        )
        receipt = await self.client.verif_tx(tx_hash=tx)
        return receipt