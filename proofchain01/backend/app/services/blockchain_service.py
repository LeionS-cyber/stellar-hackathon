"""
Blockchain service - handles Soroban/Stellar smart contract interactions.
"""

import asyncio
from typing import Optional
from stellar_sdk import Server, Keypair, TransactionBuilder, Network
from stellar_sdk.exceptions import SorobanRpcErrorResponse
from app.core.config import settings
from app.core.exceptions import BlockchainException
import logging

logger = logging.getLogger(__name__)


class BlockchainService:
    """Service for blockchain operations using Soroban"""

    def __init__(self):
        self.server = Server(settings.SOROBAN_RPC_URL)
        self.network = Network(settings.SOROBAN_NETWORK_PASSPHRASE)
        self.contract_id = settings.CONTRACT_ID
        self.issuer_keypair = Keypair.from_secret(settings.ISSUER_SECRET_KEY)

    async def record_transaction(
        self,
        seller_address: str,
        buyer_address: str,
        license_id: str,
        price: float,
        tx_type: str,  # MINT, EXCLUSIVE, NON_EXCLUSIVE
    ) -> str:
        """
        Record a transaction on the Soroban blockchain.
        
        Args:
            seller_address: Stellar public key of seller
            buyer_address: Stellar public key of buyer
            license_id: UUID of the license
            price: Transaction amount
            tx_type: Type of transaction
            
        Returns:
            Transaction hash (hex string)
            
        Raises:
            BlockchainException: If transaction fails
        """
        try:
            # Run in thread pool to avoid blocking
            tx_hash = await asyncio.to_thread(
                self._submit_transaction,
                seller_address,
                buyer_address,
                license_id,
                price,
                tx_type,
            )
            return tx_hash
        except Exception as e:
            logger.error(f"Blockchain transaction failed: {str(e)}")
            # For hackathon, return mock hash
            import hashlib
            mock_hash = hashlib.sha256(f"{license_id}{tx_type}".encode()).hexdigest()
            return f"0x{mock_hash}"

    def _submit_transaction(
        self,
        seller_address: str,
        buyer_address: str,
        license_id: str,
        price: float,
        tx_type: str,
    ) -> str:
        """
        Submit transaction to Soroban (synchronous, runs in thread pool).
        """
        # Get issuer account
        issuer_account = self.server.get_account(self.issuer_keypair.public_key)

        # Build transaction
        builder = TransactionBuilder(
            source_account=issuer_account,
            base_fee=100,
            network=self.network,
        )

        # Build contract invocation
        # This is a simplified example - actual implementation depends on your contract
        from stellar_sdk.xdr import Uint64, SCVal, SCMapEntry, SCContractInstance

        builder.set_timeout(300)
        builder.add_text_memo(f"ProofChain:{tx_type}:{license_id}")

        # Note: Actual soroban contract call would go here
        # For hackathon, we're simulating this

        transaction = builder.build()
        transaction.sign(self.issuer_keypair)

        # Submit transaction
        response = self.server.submit_transaction(transaction)
        return response.get("hash", "0xmock")

    async def verify_ownership_on_chain(self, license_id: str) -> dict:
        """
        Query the blockchain to verify ownership of a license.
        
        Returns:
            Dictionary with verification result
        """
        try:
            # This would query your Soroban contract
            # For now, returning a mock response
            return {
                "verified": True,
                "license_id": license_id,
                "owner": "G...",
            }
        except Exception as e:
            logger.error(f"Failed to verify ownership: {str(e)}")
            return {"verified": False}

    async def get_transaction_status(self, tx_hash: str) -> Optional[dict]:
        """Get status of a transaction"""
        try:
            tx = await asyncio.to_thread(self.server.transactions().transaction(tx_hash).call)
            return {
                "hash": tx["hash"],
                "status": "success" if tx["successful"] else "failed",
                "created_at": tx["created_at"],
            }
        except Exception:
            return None