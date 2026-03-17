"""
Configuration and State Management Module for Live Portfolio Tracker.

This module handles environment variable loading, global configuration settings,
and validation for the portfolio tracking application.

Example .env file structure:
----------------------------------------
# Alpha Vantage API Key (for financial data)
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Optional: Database configuration
# DATABASE_URL=postgresql://user:password@localhost/portfolio_db
# REDIS_URL=redis://localhost:6379/0

# Optional: Logging configuration
# LOG_LEVEL=INFO
# LOG_FILE=portfolio_tracker.log
----------------------------------------
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PortfolioConfig:
    """
    Configuration class for the Live Portfolio Tracker application.
    
    This class holds all global configuration settings and provides
    validation for required environment variables.
    
    Attributes:
        alpha_vantage_api_key (Optional[str]): API key for Alpha Vantage service
        default_data_source (str): Default data source for financial data
        default_currency (str): Default currency for portfolio valuation
        refresh_interval_seconds (int): Interval for data refresh in seconds
        environment (str): Current environment (development, production, testing)
        debug_mode (bool): Whether debug mode is enabled
    """
    
    # Environment variables
    alpha_vantage_api_key: Optional[str] = None
    
    # Global settings
    default_data_source: str = "yfinance"
    default_currency: str = "USD"
    refresh_interval_seconds: int = 60
    environment: str = "development"
    debug_mode: bool = False
    
    # Additional configuration (can be extended)
    _additional_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        self._validate_config()
        self._setup_logging()
    
    def _validate_config(self) -> None:
        """
        Validate configuration settings and environment variables.
        
        Logs warnings for missing optional variables and raises exceptions
        only for critical missing variables that would prevent the app from running.
        """
        # Check for Alpha Vantage API key (warn if missing but don't crash)
        if not self.alpha_vantage_api_key:
            logger.warning(
                "ALPHA_VANTAGE_API_KEY environment variable is not set. "
                "Alpha Vantage data source will not be available. "
                "Set it in your .env file or environment variables."
            )
        else:
            logger.info("Alpha Vantage API key loaded successfully")
        
        # Validate refresh interval
        if self.refresh_interval_seconds < 10:
            logger.warning(
                f"Refresh interval ({self.refresh_interval_seconds}s) is very short. "
                "Consider increasing to at least 10 seconds to avoid rate limiting."
            )
        
        # Validate currency
        valid_currencies = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD"]
        if self.default_currency not in valid_currencies:
            logger.warning(
                f"Currency '{self.default_currency}' is not in the recommended list: {valid_currencies}"
            )
    
    def _setup_logging(self) -> None:
        """Configure logging based on environment and debug mode."""
        if self.debug_mode:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
        else:
            logging.getLogger().setLevel(logging.INFO)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key to retrieve
            default: Default value if key is not found
            
        Returns:
            The configuration value or default if not found
        """
        # Check main attributes first
        if hasattr(self, key):
            return getattr(self, key)
        
        # Check additional configuration
        return self._additional_config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key to set
            value: Value to set
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self._additional_config[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary (excluding sensitive data).
        
        Returns:
            Dictionary representation of configuration
        """
        config_dict = {
            "default_data_source": self.default_data_source,
            "default_currency": self.default_currency,
            "refresh_interval_seconds": self.refresh_interval_seconds,
            "environment": self.environment,
            "debug_mode": self.debug_mode,
        }
        
        # Add additional configuration
        config_dict.update(self._additional_config)
        
        return config_dict
    
    def __str__(self) -> str:
        """String representation of configuration (excluding sensitive data)."""
        config_info = self.to_dict()
        return f"PortfolioConfig({config_info})"


def load_environment_variables() -> PortfolioConfig:
    """
    Load environment variables and create configuration instance.
    
    This function:
    1. Loads variables from .env file (if present)
    2. Loads variables from system environment
    3. Creates and returns a PortfolioConfig instance
    
    Returns:
        PortfolioConfig: Configured instance with loaded environment variables
    """
    # Load environment variables from .env file
    env_loaded = load_dotenv()
    
    if env_loaded:
        logger.info("Environment variables loaded from .env file")
    else:
        logger.info("No .env file found, using system environment variables")
    
    # Get environment variables with defaults
    alpha_vantage_api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    # Get optional configuration
    environment = os.getenv("ENVIRONMENT", "development")
    debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # Override defaults with environment variables if present
    default_data_source = os.getenv("DEFAULT_DATA_SOURCE", "yfinance")
    default_currency = os.getenv("DEFAULT_CURRENCY", "USD")
    
    # Parse refresh interval (ensure it's an integer)
    try:
        refresh_interval = int(os.getenv("REFRESH_INTERVAL_SECONDS", "60"))
    except ValueError:
        logger.warning("Invalid REFRESH_INTERVAL_SECONDS, using default 60 seconds")
        refresh_interval = 60
    
    # Create configuration instance
    config = PortfolioConfig(
        alpha_vantage_api_key=alpha_vantage_api_key,
        default_data_source=default_data_source,
        default_currency=default_currency,
        refresh_interval_seconds=refresh_interval,
        environment=environment,
        debug_mode=debug_mode,
    )
    
    return config


# Global configuration instance
# This is the main configuration object that should be imported and used throughout the app
config: PortfolioConfig = load_environment_variables()


if __name__ == "__main__":
    # Test the configuration module
    print("=" * 50)
    print("Live Portfolio Tracker - Configuration Module Test")
    print("=" * 50)
    
    print(f"\nConfiguration loaded:")
    print(f"  Default Data Source: {config.default_data_source}")
    print(f"  Default Currency: {config.default_currency}")
    print(f"  Refresh Interval: {config.refresh_interval_seconds} seconds")
    print(f"  Environment: {config.environment}")
    print(f"  Debug Mode: {config.debug_mode}")
    
    if config.alpha_vantage_api_key:
        print(f"  Alpha Vantage API Key: {'*' * 8}{config.alpha_vantage_api_key[-4:]}")
    else:
        print(f"  Alpha Vantage API Key: Not set")
    
    print(f"\nConfiguration as dictionary:")
    for key, value in config.to_dict().items():
        print(f"  {key}: {value}")
    
    print("\n" + "=" * 50)
    print("Configuration test completed successfully!")
    print("=" * 50)