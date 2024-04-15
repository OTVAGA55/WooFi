import os, sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent.absolute()
else:
    ROOT_DIR = Path(__file__).parent.absolute()

ABIS_DIR = os.path.join(ROOT_DIR, 'abis')

TOKEN_ABI = os.path.join(ABIS_DIR, 'eth_token_abi.json')
WOOFI_ABI = os.path.join(ABIS_DIR, 'woofi_swap.json') # simple swap
ONEINCH_ABI = os.path.join(ABIS_DIR, '1inchV5router.json')
WOOFI_CCS_ABI = os.path.join(ABIS_DIR, 'woofi_ccs.json') # cross chain swap
STARGATE_ROUTER_ABI = os.path.join(ABIS_DIR, 'stargate_router.json')
