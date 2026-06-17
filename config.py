"""
Configuration module for Farabixo API Request Sender
Handles environment variables and configuration loading
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for API and request settings"""
    
    # API Configuration
    API_URL = os.getenv('API_URL', 'https://gateway.example.com/api/v2/orders')
    API_TOKEN = os.getenv('API_TOKEN', '')
    
    # Request Payload Configuration
    INSTRUMENT_IDENTIFICATION = os.getenv('INSTRUMENT_IDENTIFICATION', 'BTCUSDT')
    ORDER_SIDE = int(os.getenv('ORDER_SIDE', '1'))
    QUANTITY = int(os.getenv('QUANTITY', '1289'))
    PRICE = int(os.getenv('PRICE', '29900'))
    
    @staticmethod
    def get_headers():
        """Get request headers with authentication"""
        if not Config.API_TOKEN:
            raise ValueError("⚠️ API_TOKEN not found in .env file. Please set it before running.")
        
        return {
            "Authorization": f"Bearer {Config.API_TOKEN}",
            "Content-Type": "application/json",
        }
    
    @staticmethod
    def get_base_payload():
        """Get base request payload with configuration values"""
        return {
            "orderExecutionType": "Desktop-Helium-Order",
            "instrumentIdentification": Config.INSTRUMENT_IDENTIFICATION,
            "orderSide": Config.ORDER_SIDE,
            "parentId": 0,
            "investorBourseCodeId": 0,
            "validateAssetOnSell": False,
            "quantity": Config.QUANTITY,
            "price": Config.PRICE,
            "validityDate": None,
            "validityType": 1,
            "deviceType": 1,
            "strategyLegs": None
        }
    
    @staticmethod
    def validate():
        """Validate all required configuration"""
        if not Config.API_TOKEN:
            raise ValueError("❌ Error: API_TOKEN is not set in .env file")
        return True
