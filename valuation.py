"""
Module 4: Portfolio Valuation Engine for Live Portfolio Tracker

This module handles multi-currency portfolio valuation using live market data
and foreign exchange rates. It provides accurate valuation of portfolios
containing assets denominated in different currencies.

Requirements:
    pip install yfinance pandas

Example usage:
    >>> from valuation import ValuationEngine
    >>> from portfolio_manager import PortfolioManager
    >>> from market_data import MarketDataFetcher
    
    >>> manager = PortfolioManager()
    >>> positions = manager.load_from_csv('portfolio.csv')
    >>> fetcher = MarketDataFetcher()
    >>> live_prices = fetcher.get_live_prices([p.ticker for p in positions])
    
    >>> engine = ValuationEngine()
    >>> valuation_df = engine.evaluate_portfolio(positions, live_prices)
    >>> print(valuation_df)

Note:
    - Handles missing prices or FX rates gracefully (fills with NaN)
    - Caches FX rates to avoid spamming the API
    - Converts all values to config.default_currency for consistent reporting
"""

import logging
import time
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np

# Import configuration and data classes
try:
    from config import config
    from portfolio_manager import PortfolioPosition
    from market_data import PriceData
except ImportError:
    # Fallback if modules are not available
    import logging
    logging.basicConfig(level=logging.INFO)
    config = None
    PortfolioPosition = None
    PriceData = None

# Configure module-specific logger
logger = logging.getLogger(__name__)


class ValuationEngine:
    """
    Engine for evaluating multi-currency portfolios.
    
    This class provides methods to evaluate portfolio positions across
    different currencies, converting all values to a base currency for
    consistent reporting and analysis.
    
    Attributes:
        _fx_cache (Dict[str, Tuple[float, float]]): Cache for FX rates
        _fx_cache_ttl (int): Time-to-live for FX cache in seconds
    """
    
    def __init__(self, fx_cache_ttl: int = 300):
        """
        Initialize the valuation engine.
        
        Args:
            fx_cache_ttl: Time-to-live for FX rate cache in seconds (default: 5 minutes)
        """
        self._fx_cache: Dict[str, Tuple[float, float]] = {}
        self._fx_cache_ttl = fx_cache_ttl
        
        # Try to import yfinance, but don't fail immediately
        self._yfinance_available = False
        try:
            import yfinance as yf
            self._yfinance_available = True
            logger.info("yfinance library available for FX rate fetching")
        except ImportError:
            logger.warning(
                "yfinance library not installed. "
                "Please install it with: pip install yfinance"
            )
        
        logger.debug(f"ValuationEngine initialized with FX cache TTL: {fx_cache_ttl}s")
    
    def get_fx_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Get foreign exchange rate between two currencies.
        
        Uses yfinance to fetch live conversion rates (e.g., INRUSD=X for INR to USD).
        Caches rates to avoid spamming the API.
        
        Args:
            from_currency: Source currency code (e.g., 'INR', 'EUR')
            to_currency: Target currency code (e.g., 'USD', 'GBP')
            
        Returns:
            Exchange rate (1 unit of from_currency = X units of to_currency)
            Returns NaN if rate cannot be fetched
            
        Example:
            >>> engine.get_fx_rate('INR', 'USD')
            0.012  # 1 INR = 0.012 USD
        """
        if from_currency == to_currency:
            return 1.0
        
        # Normalize currency codes
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Check cache first
        cache_key = f"{from_currency}_{to_currency}"
        current_time = time.time()
        
        if cache_key in self._fx_cache:
            rate, cache_time = self._fx_cache[cache_key]
            if current_time - cache_time < self._fx_cache_ttl:
                logger.debug(f"Using cached FX rate: {from_currency}->{to_currency} = {rate}")
                return rate
        
        if not self._yfinance_available:
            logger.warning(f"yfinance not available, cannot fetch FX rate for {from_currency}->{to_currency}")
            return float('nan')
        
        try:
            import yfinance as yf
            
            # Construct ticker for currency pair
            # yfinance uses format like INRUSD=X for INR to USD
            ticker = f"{from_currency}{to_currency}=X"
            
            logger.debug(f"Fetching FX rate for {ticker}")
            fx_ticker = yf.Ticker(ticker)
            
            # Get current price (which is the exchange rate)
            info = fx_ticker.info
            rate = None
            
            # Try different price fields
            price_fields = ['regularMarketPrice', 'currentPrice', 'ask', 'bid', 'previousClose']
            for field in price_fields:
                if field in info and info[field] is not None:
                    rate = info[field]
                    break
            
            if rate is None:
                logger.warning(f"No FX rate data available for {ticker}")
                return float('nan')
            
            # Validate rate
            if not isinstance(rate, (int, float)) or rate <= 0:
                logger.warning(f"Invalid FX rate for {ticker}: {rate}")
                return float('nan')
            
            rate = float(rate)
            
            # Cache the rate
            self._fx_cache[cache_key] = (rate, current_time)
            logger.info(f"Fetched FX rate: {from_currency}->{to_currency} = {rate}")
            
            return rate
            
        except Exception as e:
            logger.error(f"Error fetching FX rate for {from_currency}->{to_currency}: {e}")
            return float('nan')
    
    def evaluate_portfolio(self, 
                          positions: List[PortfolioPosition], 
                          live_prices: Dict[str, PriceData]) -> pd.DataFrame:
        """
        Evaluate portfolio positions with multi-currency support.
        
        Converts all values to the base currency (config.default_currency)
        and calculates P&L metrics.
        
        Args:
            positions: List of portfolio positions
            live_prices: Dictionary of live price data for tickers
            
        Returns:
            DataFrame with columns:
                - Ticker
                - Shares
                - Native Currency
                - Avg Cost (Native)
                - Current Price (Native)
                - Total Cost (Base Currency)
                - Current Value (Base Currency)
                - P&L ($ Base)
                - P&L (%)
            
        Note:
            - Missing prices or FX rates result in NaN values
            - All monetary values are in config.default_currency
        """
        if not positions:
            logger.warning("Empty positions list provided to evaluate_portfolio")
            return pd.DataFrame()
        
        # Get base currency from config
        base_currency = "USD"  # Default fallback
        if config and hasattr(config, 'default_currency'):
            base_currency = config.default_currency
        
        logger.info(f"Evaluating {len(positions)} positions in base currency: {base_currency}")
        
        # Prepare data for DataFrame
        data = []
        
        for position in positions:
            ticker = position.ticker
            shares = position.quantity
            avg_cost_native = position.average_price
            total_cost_native = position.total_cost
            
            # Get live price data
            price_data = live_prices.get(ticker)
            
            if price_data is None:
                logger.warning(f"No live price data for {ticker}, skipping valuation")
                # Add row with NaN for missing data
                data.append({
                    'Ticker': ticker,
                    'Shares': shares,
                    'Native Currency': 'N/A',
                    'Avg Cost (Native)': avg_cost_native,
                    'Current Price (Native)': float('nan'),
                    'Total Cost (Base Currency)': float('nan'),
                    'Current Value (Base Currency)': float('nan'),
                    'P&L ($ Base)': float('nan'),
                    'P&L (%)': float('nan')
                })
                continue
            
            native_currency = price_data.currency
            current_price_native = price_data.price
            
            # Calculate values in native currency
            current_value_native = shares * current_price_native
            
            # Convert to base currency
            total_cost_base = float('nan')
            current_value_base = float('nan')
            
            if native_currency != base_currency:
                # Need FX rate for conversion
                fx_rate_to_base = self.get_fx_rate(native_currency, base_currency)
                
                if not np.isnan(fx_rate_to_base):
                    total_cost_base = total_cost_native * fx_rate_to_base
                    current_value_base = current_value_native * fx_rate_to_base
                else:
                    logger.warning(f"No FX rate available for {native_currency}->{base_currency}")
            else:
                # Already in base currency
                total_cost_base = total_cost_native
                current_value_base = current_value_native
            
            # Calculate P&L
            pnl_dollar = float('nan')
            pnl_percent = float('nan')
            
            if not np.isnan(total_cost_base) and not np.isnan(current_value_base):
                pnl_dollar = current_value_base - total_cost_base
                if total_cost_base != 0:
                    pnl_percent = (pnl_dollar / total_cost_base) * 100
            
            # Add row to data
            data.append({
                'Ticker': ticker,
                'Shares': shares,
                'Native Currency': native_currency,
                'Avg Cost (Native)': avg_cost_native,
                'Current Price (Native)': current_price_native,
                'Total Cost (Base Currency)': total_cost_base,
                'Current Value (Base Currency)': current_value_base,
                'P&L ($ Base)': pnl_dollar,
                'P&L (%)': pnl_percent
            })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Set column order
        column_order = [
            'Ticker',
            'Shares',
            'Native Currency',
            'Avg Cost (Native)',
            'Current Price (Native)',
            'Total Cost (Base Currency)',
            'Current Value (Base Currency)',
            'P&L ($ Base)',
            'P&L (%)'
        ]
        df = df[column_order]
        
        # Add summary row
        if not df.empty:
            total_cost_sum = df['Total Cost (Base Currency)'].sum(skipna=True)
            current_value_sum = df['Current Value (Base Currency)'].sum(skipna=True)
            total_pnl_dollar = current_value_sum - total_cost_sum
            total_pnl_percent = (total_pnl_dollar / total_cost_sum * 100) if total_cost_sum != 0 else float('nan')
            
            summary_row = pd.DataFrame([{
                'Ticker': 'TOTAL',
                'Shares': df['Shares'].sum(skipna=True),
                'Native Currency': 'MULTI',
                'Avg Cost (Native)': float('nan'),
                'Current Price (Native)': float('nan'),
                'Total Cost (Base Currency)': total_cost_sum,
                'Current Value (Base Currency)': current_value_sum,
                'P&L ($ Base)': total_pnl_dollar,
                'P&L (%)': total_pnl_percent
            }])
            
            df = pd.concat([df, summary_row], ignore_index=True)
        
        logger.info(f"Portfolio evaluation completed: {len(df)-1} positions evaluated")
        return df
    
    def clear_fx_cache(self) -> None:
        """Clear the FX rate cache."""
        cache_size = len(self._fx_cache)
        self._fx_cache.clear()
        logger.debug(f"Cleared FX cache ({cache_size} entries)")
    
    def get_fx_cache_info(self) -> Dict[str, any]:
        """
        Get information about the current FX cache state.
        
        Returns:
            Dictionary with FX cache statistics
        """
        current_time = time.time()
        valid_entries = 0
        expired_entries = 0
        
        for cache_key, (rate, cache_time) in self._fx_cache.items():
            if current_time - cache_time < self._fx_cache_ttl:
                valid_entries += 1
            else:
                expired_entries += 1
        
        return {
            'total_entries': len(self._fx_cache),
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_ttl_seconds': self._fx_cache_ttl
        }
    
    def __str__(self) -> str:
        """String representation of the valuation engine."""
        cache_info = self.get_fx_cache_info()
        return (f"ValuationEngine(FX cache: {cache_info['total_entries']} entries, "
                f"{cache_info['valid_entries']} valid)")


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("Portfolio Valuation Module - Test")
    print("=" * 60)
    
    print("\nNote: This module requires yfinance and pandas libraries.")
    print("Install them with: pip install yfinance pandas")
    print()
    
    try:
        # Import required modules
        from portfolio_manager import PortfolioManager, PortfolioPosition
        from market_data import MarketDataFetcher, PriceData
        
        # Create a valuation engine
        engine = ValuationEngine()
        
        # Test 1: FX rate fetching
        print("1. Testing FX rate fetching:")
        test_pairs = [('USD', 'USD'), ('INR', 'USD'), ('EUR', 'USD')]
        for from_curr, to_curr in test_pairs:
            try:
                rate = engine.get_fx_rate(from_curr, to_curr)
                if from_curr == to_curr:
                    print(f"  {from_curr}->{to_curr}: {rate:.4f} (should be 1.0)")
                else:
                    print(f"  {from_curr}->{to_curr}: {rate:.6f}")
            except Exception as e:
                print(f"  Error fetching {from_curr}->{to_curr}: {e}")
        
        # Test 2: Cache functionality
        print("\n2. Testing FX cache functionality:")
        cache_info = engine.get_fx_cache_info()
        print(f"  FX cache info: {cache_info}")
        
        # Test 3: Portfolio evaluation with mock data
        print("\n3. Testing portfolio evaluation with mock data:")
        
        # Create mock positions (mixed currencies)
        mock_positions = [
            PortfolioPosition(ticker="AAPL", quantity=10, average_price=150.25),  # USD
            PortfolioPosition(ticker="RELIANCE.NS", quantity=5, average_price=2500.50),  # INR
            PortfolioPosition(ticker="SIEMENS.NS", quantity=8, average_price=4000.75),  # INR
        ]
        
        # Create mock price data
        mock_prices = {
            "AAPL": PriceData(ticker="AAPL", price=175.50, currency="USD"),
            "RELIANCE.NS": PriceData(ticker="RELIANCE.NS", price=2800.25, currency="INR"),
            "SIEMENS.NS": PriceData(ticker="SIEMENS.NS", price=4200.50, currency="INR"),
        }
        
        try:
            valuation_df = engine.evaluate_portfolio(mock_positions, mock_prices)
            print("\n  Portfolio Valuation Results:")
            print(valuation_df.to_string())
            
            print("\n  Column descriptions:")
            print("  - Ticker: Stock symbol")
            print("  - Shares: Number of shares held")
            print("  - Native Currency: Currency of the stock")
            print("  - Avg Cost (Native): Average purchase price in native currency")
            print("  - Current Price (Native): Current market price in native currency")
            print("  - Total Cost (Base Currency): Total investment converted to base currency (USD)")
            print("  - Current Value (Base Currency): Current value converted to base currency (USD)")
            print("  - P&L ($ Base): Profit/Loss in base currency")
            print("  - P&L (%): Profit/Loss percentage")
            
        except Exception as e:
            print(f"  Error evaluating portfolio: {e}")
        
        # Test 4: Clear cache
        print("\n4. Testing cache clearing:")
        engine.clear_fx_cache()
        cache_info = engine.get_fx_cache_info()
        print(f"  FX cache after clearing: {cache_info}")
        
        # Test 5: Missing data handling
        print("\n5. Testing missing data handling:")
        positions_with_missing = [
            PortfolioPosition(ticker="AAPL", quantity=10, average_price=150.25),
            PortfolioPosition(ticker="MISSING", quantity=5, average_price=100.0),
        ]
        
        prices_with_missing = {
            "AAPL": PriceData(ticker="AAPL", price=175.50, currency="USD"),
            # MISSING ticker not in prices
        }
        
        try:
            valuation_df = engine.evaluate_portfolio(positions_with_missing, prices_with_missing)
            print("\n  Valuation with missing price data:")
            print(valuation_df.to_string())
            print("  Note: Missing tickers show NaN values")
        except Exception as e:
            print(f"  Error: {e}")
        
        print("\n" + "=" * 60)
        print("Valuation Module test completed!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"\nError: {e}")
        print("\nTo run this module, install required libraries:")
        print("  pip install yfinance pandas")
        print("\n" + "=" * 60)
        print("Installation required to complete test")
        print("=" * 60)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("\n" + "=" * 60)
        print("Test completed with errors")
        print("=" * 60)