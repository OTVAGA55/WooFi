from web3 import Web3, AsyncWeb3, Account
from web3.middleware import geth_poa_middleware
from web3.eth import AsyncEth
from typing import Optional, Any
import requests, asyncio, aiohttp, time, random

from data.models import TokenAmount, Network
from libs.utils import read_json, async_get
from data.config import TOKEN_ABI

class Client:
    default_abi = read_json(TOKEN_ABI)

    def __init__(
        self,
        wallet: Account,
        network: Network
    ):
        self.wallet = wallet
        self.private_key = self.wallet._private_key
        self.network = network
        self.w3 = Web3(
            provider=Web3.AsyncHTTPProvider(
                endpoint_uri=self.network.rpc
            ),
            modules={
                'eth': (AsyncEth,)
            },
            middlewares=[]
        )
        self.address = Web3.to_checksum_address(wallet.address)

    # decimals of contract
    async def get_decimals(self, contract_address: str) -> int:
        await asyncio.sleep(random.random() * 2)
        return await self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=Client.default_abi
        ).functions.decimals().call()

    # balance of NOT native token
    async def balance_of(self, contract_address: str, address: Optional[str] = None) -> TokenAmount:
        if not address:
            address = self.address
        await asyncio.sleep(random.random() * 2)
        contract = self.w3.eth.contract(
            address=contract_address,
            abi=Client.default_abi
        )
        amount = await contract.functions.balanceOf(address).call()
        decimals = await self.get_decimals(contract_address=contract_address)

        return TokenAmount(
            amount=amount,
            decimals=decimals,
            wei=True
        )

    # return amount of allowed amount to spender contract
    async def get_allowance(self, token_address: str, spender: str):
        await asyncio.sleep(random.random() * 2)
        allowance = await self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=Client.default_abi
        ).functions.allowance(self.address, spender).call()

        decimals = await self.get_decimals(contract_address=token_address)
        
        return TokenAmount(
            amount=allowance,
            decimals=decimals,
            wei=True
        )

    async def check_balance_interface(self, token_address: str, min_value: int) -> bool:
        await asyncio.sleep(random.random() * 2)
        # print(f'{self.address} | balanceOf [START] | checking balance of {token_address}')
        balance = await self.balance_of(contract_address=token_address)
        decimals = await self.get_decimals(contract_address=token_address)
        if balance.Wei < min_value * 10 ** decimals:
            print(f"{self.address} | balanceOf [END] | not enough of {token_address}")
            return False
        return True
    
    def simple_transfer(self, to_address: str, value):
        self.send_transaction(to=to_address, value=value)

    @staticmethod
    async def get_max_priority_fee_per_gas(w3: Web3, block: dict) -> int:
        block_number = block['number']
        latest_block_transation_count = await w3.eth.get_block_transaction_count(block_number)
        
        max_priority_fee_per_gas_list = []
        for tx in range(latest_block_transation_count):
            try:
                transaction = await w3.eth.get_transaction_by_block(block_number, tx)
                if 'maxPriorityFeePerGas' in tx:
                    max_priority_fee_per_gas_list.append(transaction['maxPriorityFeePerGas'])
            except Exception:
                continue
        
        if not max_priority_fee_per_gas_list:
            max_priority_fee_per_gas = w3.eth.max_priority_fee
        else:
            max_priority_fee_per_gas_list.sort()
            max_priority_fee_per_gas = max_priority_fee_per_gas_list[len(max_priority_fee_per_gas_list) // 2]
        
        return max_priority_fee_per_gas

    async def send_transaction(
        self,
        to,
        data=None,
        from_=None,
        increase_gas=1.05,
        value=None,
        max_priority_fee_per_gas: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None
    ):
        if not from_:
            from_ = self.address

        # nonce = await self.w3.eth.get_transaction_count(self.address)
        chain_id = await self.w3.eth.chain_id
        nonce = await self.w3.eth.get_transaction_count(self.address)
        tx_params = {
            "chainId": chain_id,
            "nonce": nonce,
            "from": Web3.to_checksum_address(from_),
            "to": Web3.to_checksum_address(to),
        }
        if data:
            tx_params["data"] = data
        
        if self.network.eip1559_tx:
            w3 = AsyncWeb3(
                provider=Web3.AsyncHTTPProvider(
                    endpoint_uri=self.network.rpc,
                ),
                modules={
                    'eth': (AsyncEth,)
                },
                middlewares=[]
            )
            # w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            last_block = await w3.eth.get_block('latest')
            if not max_priority_fee_per_gas:
                max_priority_fee_per_gas = await self.w3.eth.max_priority_fee
            
            if not max_fee_per_gas:
                base_fee = int(last_block['baseFeePerGas'] * increase_gas)
                max_fee_per_gas = base_fee + max_priority_fee_per_gas
            
            tx_params['maxPriorityFeePerGas'] = max_priority_fee_per_gas
            tx_params['maxFeePerGas'] = max_fee_per_gas
        else:
            tx_params['gasPrice'] = await self.w3.eth.gas_price

        if value:
            tx_params['value'] = value

        try:
            tx_params['gas'] = int(await self.w3.eth.estimate_gas(tx_params) * increase_gas)
        except Exception as err:
            print(f"{self.address} | Transaction failed | {err}")
            return None
        """
            Три основные ошибки, которые могут быть после estimate_gas:
                1. Маленькое value
                2. Ошибка в data
                3. Мало газа
        """
                
        if (await self.w3.eth.get_transaction_count(self.address)) > nonce:
            tx_params['nonce'] = await self.w3.eth.get_transaction_count(self.address)

        sign = self.wallet.sign_transaction(tx_params)
        return await self.w3.eth.send_raw_transaction(sign.rawTransaction)
   
    async def verif_tx(self, tx_hash):
        try:
            data = await self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=200)
            if 'status' in data and data['status'] == 1:
                print(f"{self.address} | Transaction was successful: {tx_hash.hex()}")
                return True
            else:
                print(f"{self.address} | Transaction failed {data['transactionHash'].hex()}")
                return False
        except Exception as err:
            print(f"{self.address} | Unexpected error in <verif_tx> func: {err}")
            return False

    async def approve(self, token_address, spender, amount: Optional[TokenAmount] = None):
        contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=Client.default_abi
        )
        return await self.send_transaction(
            to=token_address,
            data=contract.encodeABI(
                'approve',
                args=(spender, amount.Wei)
            )
        )
    
    async def approve_interface(self, token_address: str, spender: str, amount: Optional[TokenAmount] = None) -> bool:
        print(f"{self.address} | Approving {token_address} for spender {spender}...")
        
        decimals = await self.get_decimals(contract_address=token_address)
        balance = await self.balance_of(contract_address=token_address)

        if balance.Wei <= 0:
            print(f"{self.address} | Approve | balance = 0")
            return False
        
        if not amount or amount.Wei > balance.Wei:
            amount = balance

        approved = await self.get_allowance(token_address=token_address, spender=spender)

        if amount.Wei <= approved.Wei:
            print(f"{self.address} | Approve | already approved")
            return True
        
        tx_hash = await self.approve(token_address=token_address, spender=spender, amount=amount)
        
        if not (await self.verif_tx(tx_hash=tx_hash)):
            print(f"{self.address} | Approve ERROR | {token_address} for spender {spender}")
            return False
        else:
            return True
        
    
    async def get_eth_price(self, token='ETH'):
        token = token.upper()
        binance_api_url = f'https://api.binance.com/api/v3/depth?limit=1&symbol={token}USDT'
        
        response = await async_get(url=binance_api_url)
                
        if 'asks' not in response:
            print(f"\tcode: {response.status} | asks not in response | json: {response}")
            return False
        
        return float(response['asks'][0][0])