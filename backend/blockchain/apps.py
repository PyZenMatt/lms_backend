"""
Blockchain Django App Configuration

This module configures the blockchain Django application for TeoCoin
token management and blockchain operations.
"""

from django.apps import AppConfig


class BlockchainConfig(AppConfig):
    """
    Configuration for the Blockchain Django application.
    
    This app provides TeoCoin token integration including wallet management,
    token minting, balance queries, and transaction tracking on the
    Polygon Amoy testnet.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blockchain'
    verbose_name = 'Blockchain & TeoCoin Management'
    
    def ready(self):
        """
        Initialize the blockchain app when Django starts.
        
        This method is called when the app is ready and can be used
        to set up signals, initialize blockchain connections, or
        perform other startup tasks.
        """
        # Import any signals or initialization code here
        pass
