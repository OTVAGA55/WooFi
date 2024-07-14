## Asynchronous automation WooFi protocol in Arbitrum network

This script will help you, if you need to transfer or stake tokens in multiple wallets very fast.
It only works in Arbitrum network for now.

Python version - **3.10.4**
### Functions:
- Swap **$ETH** to **$USDC**
- Swap **$USDC** to **$ETH**
- Swap **$ETH** to **$WOO**
- Cross-chain swap Arbitrum **$ETH** to Polygon **$ETH**
- Stake **$WOO**
- Unstake **$WOO**

All functions you can find in tasks/woofi.py

### How to run?
1. Create virtual environment and install all requirements
2. Add wallets.txt in data directory and put your private keys there
3. In main.py set amount and needed operations to do and follow instructions there
4. Run main.py