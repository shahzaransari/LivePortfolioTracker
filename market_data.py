"""
Module 3: Live Market Data Ingestion for Live Portfolio Tracker

This module handles fetching real-time market data using the yfinance library.
It provides efficient batch fetching of stock prices with robust error handling.

Requirements:
    pip install yfinance

Example usage:
    >>> from market_data import MarketDataFetcher
    >>> fetcher = MarketDataFetcher()
    >>> prices = fetcher.get_live_prices(['AAPL', 'MSFT', 'GOOGL'])
    >>> print(prices)
    {'AAPL': 175.50, 'MSFT': 410.20, 'GOOGL': 2800.75}

Note:
    - Network requests may fail; the module includes retry logic and error handling
    - Invalid tickers are logged and omitted from results rather than crashing the batch
    - Prices are fetched in USD by default
"""

import logging
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# Import configuration from existing config module
try:
    from config import config
except ImportError:
    # Fallback if config module is not available
    import logging
    logging.basicConfig(level=logging.INFO)
    config = None

# Configure module-specific logger
logger = logging.getLogger(__name__)


@dataclass
class MarketDataConfig:
    """
    Configuration for market data fetching.
    
    Attributes:
        max_retries (int): Maximum number of retry attempts for failed requests
        retry_delay_seconds (float): Delay between retry attempts in seconds
        request_timeout_seconds (int): Timeout for individual requests in seconds
        batch_size (int): Maximum number of tickers to fetch in a single batch
        cache_ttl_seconds (int): Time-to-live for cached prices in seconds
        default_currency (str): Default currency for price data
    """
    
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    request_timeout_seconds: int = 10
    batch_size: int = 50  # yfinance can handle up to ~100 tickers per request
    cache_ttl_seconds: int = 30  # Cache prices for 30 seconds
    default_currency: str = "USD"
    
    def __post_init__(self):
        """Validate configuration settings."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must be non-negative")
        if self.request_timeout_seconds <= 0:
            raise ValueError("request_timeout_seconds must be positive")
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds must be non-negative")


@dataclass
class PriceData:
    """
    Data class representing price information for a single ticker.
    
    Attributes:
        ticker (str): Stock ticker symbol
        price (float): Current market price
        currency (str): Currency of the price
        timestamp (datetime): When the price was fetched
        source (str): Data source (e.g., 'yfinance')
    """
    
    ticker: str
    price: float
    currency: str = "USD"
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "yfinance"
    
    def __post_init__(self):
        """Post-initialization validation."""
        self.ticker = self.ticker.upper().strip()
        if self.price <= 0:
            raise ValueError(f"Price must be positive, got {self.price}")
    
    def to_dict(self) -> Dict[str, any]:
        """Convert price data to dictionary representation."""
        return {
            'ticker': self.ticker,
            'price': self.price,
            'currency': self.currency,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }
    
    def __str__(self) -> str:
        """String representation of price data."""
        return f"{self.ticker}: ${self.price:.2f} {self.currency} ({self.timestamp.strftime('%H:%M:%S')})"


class MarketDataFetcher:
    """
    Main class for fetching live market data.
    
    This class provides methods to efficiently fetch current market prices
    for multiple tickers with robust error handling and caching.
    
    Attributes:
        config (MarketDataConfig): Configuration for data fetching
        _cache (Dict[str, Tuple[PriceData, float]]): Internal cache for prices
    """
    
    def __init__(self, config: Optional[MarketDataConfig] = None):
        """
        Initialize the market data fetcher.
        
        Args:
            config: Optional MarketDataConfig instance. If not provided,
                   uses default configuration.
        """
        self.config = config or MarketDataConfig()
        self._cache: Dict[str, Tuple[PriceData, float]] = {}
        
        # Try to import yfinance, but don't fail immediately
        self._yfinance_available = False
        try:
            import yfinance as yf
            self._yfinance_available = True
            logger.info("yfinance library available for market data fetching")
        except ImportError:
            logger.warning(
                "yfinance library not installed. "
                "Please install it with: pip install yfinance"
            )
        
        logger.debug(f"MarketDataFetcher initialized with config: {self.config}")
    
    def get_live_prices(self, tickers: List[str]) -> Dict[str, PriceData]:
        """
        Fetch live market prices for the given tickers.
        
        This method efficiently fetches current market prices for all requested
        tickers, handling errors gracefully and using caching where appropriate.
        
        Args:
            tickers: List of ticker symbols to fetch prices for
            
        Returns:
            Dictionary mapping ticker symbols to PriceData objects.
            Invalid tickers are omitted from the result.
            
        Example:
            >>> fetcher = MarketDataFetcher()
            >>> prices = fetcher.get_live_prices(['AAPL', 'MSFT', 'FAKE_TICKER'])
            >>> # Returns {'AAPL': PriceData(...), 'MSFT': PriceData(...)}
            >>> # FAKE_TICKER is omitted and logged as warning
            
        Raises:
            ImportError: If yfinance is not installed
            RuntimeError: If all retry attempts fail for all tickers
        """
        if not self._yfinance_available:
            raise ImportError(
                "yfinance library is not installed. "
                "Please install it with: pip install yfinance"
            )
        
        if not tickers:
            logger.warning("Empty ticker list provided to get_live_prices")
            return {}
        
        # Clean and deduplicate tickers
        unique_tickers = list(set(ticker.upper().strip() for ticker in tickers))
        logger.debug(f"Fetching prices for {len(unique_tickers)} unique tickers")
        
        # Separate cached and uncached tickers
        cached_prices = {}
        uncached_tickers = []
        
        current_time = time.time()
        for ticker in unique_tickers:
            if ticker in self._cache:
                price_data, cache_time = self._cache[ticker]
                if current_time - cache_time < self.config.cache_ttl_seconds:
                    cached_prices[ticker] = price_data
                    logger.debug(f"Using cached price for {ticker}: ${price_data.price:.2f} {price_data.currency}")
                else:
                    uncached_tickers.append(ticker)
            else:
                uncached_tickers.append(ticker)
        
        # Fetch uncached tickers
        if uncached_tickers:
            fetched_prices = self._fetch_prices_with_retry(uncached_tickers)
            # Update cache with new prices
            for ticker, price_data in fetched_prices.items():
                self._cache[ticker] = (price_data, current_time)
            
            # Combine cached and fetched prices
            result = {**cached_prices, **fetched_prices}
        else:
            result = cached_prices
        
        logger.info(f"Successfully fetched prices for {len(result)}/{len(unique_tickers)} tickers")
        return result
    
    def _fetch_prices_with_retry(self, tickers: List[str]) -> Dict[str, PriceData]:
        """
        Fetch prices with retry logic for network failures.
        
        Args:
            tickers: List of ticker symbols to fetch
            
        Returns:
            Dictionary of successfully fetched PriceData objects
            
        Raises:
            RuntimeError: If all retry attempts fail
        """
        import yfinance as yf
        
        # Split into batches if needed
        batches = [
            tickers[i:i + self.config.batch_size]
            for i in range(0, len(tickers), self.config.batch_size)
        ]
        
        all_results = {}
        failed_batches = []
        
        for batch_num, batch in enumerate(batches, 1):
            logger.debug(f"Processing batch {batch_num}/{len(batches)} with {len(batch)} tickers")
            
            for attempt in range(self.config.max_retries + 1):
                try:
                    batch_results = self._fetch_single_batch(batch)
                    all_results.update(batch_results)
                    logger.debug(f"Batch {batch_num} successful: {len(batch_results)} prices fetched")
                    break
                except Exception as e:
                    if attempt == self.config.max_retries:
                        logger.error(
                            f"Failed to fetch batch {batch_num} after {self.config.max_retries + 1} attempts: {e}"
                        )
                        failed_batches.append(batch)
                    else:
                        logger.warning(
                            f"Attempt {attempt + 1}/{self.config.max_retries + 1} failed for batch {batch_num}: {e}"
                        )
                        if attempt < self.config.max_retries:
                            time.sleep(self.config.retry_delay_seconds)
        
        # Log warnings for any completely failed batches
        if failed_batches:
            failed_tickers = [ticker for batch in failed_batches for ticker in batch]
            logger.warning(
                f"Failed to fetch prices for {len(failed_tickers)} tickers after all retries: {failed_tickers}"
            )
        
        return all_results
    
    def _fetch_single_batch(self, tickers: List[str]) -> Dict[str, PriceData]:
        """
        Fetch prices for a single batch of tickers.
        
        Args:
            tickers: List of ticker symbols in this batch
            
        Returns:
            Dictionary of successfully fetched PriceData objects
            
        Raises:
            Exception: If the fetch operation fails
        """
        import yfinance as yf
        
        try:
            # Create ticker objects
            ticker_objects = yf.Tickers(" ".join(tickers))
            
            # Fetch current price data
            results = {}
            for ticker in tickers:
                try:
                    ticker_obj = ticker_objects.tickers[ticker]
                    
                    # Get the latest price
                    # Try to get regularMarketPrice first, fall back to currentPrice
                    price_data = ticker_obj.info
                    
                    price = None
                    price_fields = ['regularMarketPrice', 'currentPrice', 'ask', 'bid', 'previousClose']
                    
                    for field in price_fields:
                        if field in price_data and price_data[field] is not None:
                            price = price_data[field]
                            break
                    
                    if price is None:
                        logger.warning(f"No price data available for {ticker}")
                        continue
                    
                    # Validate price
                    if not isinstance(price, (int, float)) or price <= 0:
                        logger.warning(f"Invalid price for {ticker}: {price}")
                        continue
                    
                    # Extract currency from yfinance info
                    currency = "USD"  # Default fallback
                    currency_fields = ['currency', 'financialCurrency']
                    for field in currency_fields:
                        if field in price_data and price_data[field] is not None:
                            currency = price_data[field].upper()
                            break
                    
                    # Create PriceData object
                    price_data_obj = PriceData(
                        ticker=ticker,
                        price=float(price),
                        currency=currency
                    )
                    
                    results[ticker] = price_data_obj
                    logger.debug(f"Fetched price for {ticker}: ${price:.2f} {currency}")
                    
                except KeyError:
                    logger.warning(f"Ticker {ticker} not found in yfinance response")
                except Exception as e:
                    logger.warning(f"Error fetching price for {ticker}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching batch {tickers}: {e}")
            raise
    
    def clear_cache(self) -> None:
        """Clear the price cache."""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.debug(f"Cleared price cache ({cache_size} entries)")
    
    def get_cache_info(self) -> Dict[str, any]:
        """
        Get information about the current cache state.
        
        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for ticker, (price_data, cache_time) in self._cache.items():
            if current_time - cache_time < self.config.cache_ttl_seconds:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': len(self._cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_ttl_seconds': self.config.cache_ttl_seconds
        }
    
    def __str__(self) -> str:
        """String representation of the market data fetcher."""
        cache_info = self.get_cache_info()
        return (f"MarketDataFetcher(config={self.config}, "
                f"cache={cache_info['total_entries']} entries, "
                f"{cache_info['valid_entries']} valid)")


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("Market Data Module - Test")
    print("=" * 60)
    
    print("\nNote: This module requires yfinance library.")
    print("Install it with: pip install yfinance")
    print()
    
    try:
        # Create a market data fetcher
        fetcher = MarketDataFetcher()
        
        # Test 1: Fetch prices for real tickers
        print("1. Fetching prices for real tickers:")
        real_tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        try:
            prices = fetcher.get_live_prices(real_tickers)
            for ticker, price_data in prices.items():
                print(f"  {ticker}: ${price_data.price:.2f} {price_data.currency}")
            print(f"  Successfully fetched {len(prices)}/{len(real_tickers)} prices")
        except Exception as e:
            print(f"  Error: {e}")
            print("  Make sure yfinance is installed: pip install yfinance")
        
        # Test 2: Fetch with invalid ticker
        print("\n2. Fetching with invalid ticker (error handling test):")
        mixed_tickers = ['AAPL', 'FAKE_TICKER_XYZ', 'MSFT', 'INVALID123']
        try:
            prices = fetcher.get_live_prices(mixed_tickers)
            for ticker, price_data in prices.items():
                print(f"  {ticker}: ${price_data.price:.2f} {price_data.currency}")
            print(f"  Successfully fetched {len(prices)}/{len(mixed_tickers)} prices")
            print("  Note: Invalid tickers are omitted (logged as warnings)")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Test 3: Cache functionality
        print("\n3. Testing cache functionality:")
        cache_info = fetcher.get_cache_info()
        print(f"  Cache info: {cache_info}")
        
        # Fetch same tickers again (should use cache)
        print("  Fetching AAPL and MSFT again (should use cache):")
        try:
            prices = fetcher.get_live_prices(['AAPL', 'MSFT'])
            for ticker, price_data in prices.items():
                print(f"  {ticker}: ${price_data.price:.2f} {price_data.currency}")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Test 4: Empty ticker list
        print("\n4. Testing empty ticker list:")
        try:
            prices = fetcher.get_live_prices([])
            print(f"  Result: {prices}")
            print("  Empty dictionary returned for empty input")
        except Exception as e:
            print(f"  Error: {e}")
        
        # Test 5: Clear cache
        print("\n5. Testing cache clearing:")
        fetcher.clear_cache()
        cache_info = fetcher.get_cache_info()
        print(f"  Cache after clearing: {cache_info}")
        
        print("\n" + "=" * 60)
        print("Market Data Module test completed!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"\nError: {e}")
        print("\nTo run this module, install yfinance:")
        print("  pip install yfinance")
        print("\n" + "=" * 60)
        print("Installation required to complete test")
        print("=" * 60)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("\n" + "=" * 60)
        print("Test completed with errors")
        print("=" * 60)