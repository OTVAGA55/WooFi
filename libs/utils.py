import json, aiohttp
from typing import Union, Optional
from eth_utils import to_checksum_address
from eth_typing import ChecksumAddress

def read_json(path: str, encoding: Optional[str] = None) -> Union[list, dict]:
    return json.load(open(path, encoding=encoding))

def checksum(address: str) -> ChecksumAddress:
    return to_checksum_address(address)

async def async_get(url: str, headers: Optional[dict] = None, **kwargs) -> Optional[dict]:
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url=url, **kwargs) as resp:
            response = await resp.json()
            
            if resp.status == 200:
                return response
            
            raise Exception(f"{resp.status} - {response}")



