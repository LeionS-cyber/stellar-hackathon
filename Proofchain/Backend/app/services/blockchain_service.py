from web3 import Web3
from app.core.config import settings

class BlockchainService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URL))
        self.contract_address = settings.CONTRACT_ADDRESS
        # In a real setup, import compiled Solidity ABI
        self.abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "seller", "type": "address"},
                    {"internalType": "address", "name": "buyer", "type": "address"},
                    {"internalType": "string", "name": "licenseId", "type": "string"},
                    {"internalType": "uint256", "name": "price", "type": "uint256"},
                    {"internalType": "string", "name": "txType", "type": "string"}
                ],
                "name": "recordTransaction",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]

    async def record_transaction(self, seller: str, buyer: str, license_id: str, price: float, tx_type: str, private_key: str) -> str:
        """Records MINT, EXCLUSIVE, or NON_EXCLUSIVE transactions to the EVM testnet (e.g., Sepolia)"""
        # Hackathon Mock for Web3 transaction sending:
        # In production, use w3.eth.contract to build the tx, sign with private key and sendRawTransaction.
        
        # Mocking return Transaction Hash for the Hackathon:
        return f"0x{Web3.to_hex(Web3.keccak(text=license_id + tx_type))[2:66]}"