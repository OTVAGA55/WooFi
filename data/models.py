from decimal import Decimal
from typing import Union

class TokenAmount:
    Wei: int
    Ether: Decimal
    decimals: int

    def __init__(self, amount: Union[int, float, str, Decimal], decimals: int = 18, wei: bool = False) -> None:
        self.decimals = decimals

        if wei:
            self.Wei: int = amount
            self.Ether: Decimal = Decimal(str(amount)) / 10 ** decimals
        else:
            self.Wei: int = int(Decimal(str(amount)) * 10 ** decimals)
            self.Ether: Decimal = Decimal(str(amount))

class Network:
    def __init__(
        self,
        name: str,
        rpc: str,
        chain_id: int,
        eip1559_tx: bool,
        coin_symbol: str,
        explorer: str,
        decimals: int = 18
    ):
        self.name = name
        self.rpc = rpc
        self.chain_id = chain_id
        self.eip1559_tx = eip1559_tx
        self.coin_symbol = coin_symbol
        self.explorer = explorer
        self.decimals = decimals
    
    def __str__(self):
        return f'{self.name}'

Arbitrum = Network(
    name='arbitrum',
    rpc='https://arbitrum-one-rpc.publicnode.com',
    chain_id=42161,
    eip1559_tx=True,
    coin_symbol='ETH',
    explorer='https://arbiscan.io/',
)

Polygon = Network(
    name='polygon',
    rpc='https://polygon-bor-rpc.publicnode.com',
    chain_id=137,
    eip1559_tx=True,
    coin_symbol='MATIC',
    explorer='https://polygonscan.com/',
)

BSC = Network(
    name='bsc',
    rpc='https://bsc-mainnet.public.blastapi.io',
    chain_id=56,
    eip1559_tx=True,
    coin_symbol='BNB',
    explorer='https://bscscan.com/',
)