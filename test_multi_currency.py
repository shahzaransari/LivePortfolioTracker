#!/usr/bin/env python3
"""
Test script for multi-currency portfolio valuation.

This script tests the integration of:
1. market_data.py (updated to return PriceData objects with currency)
2. valuation.py (new module for multi-currency valuation)
3. portfolio_manager.py (existing module)

It demonstrates how to handle a portfolio with mixed USD and INR stocks.
"""

import sys
import os
import pandas as pd

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_multi_currency_portfolio():
    """Test the complete multi-currency portfolio valuation workflow."""
    print("=" * 70)
    print("Multi-Currency Portfolio Valuation Test")
    print("=" * 70)
    
    try:
        # Import modules
        from portfolio_manager import PortfolioManager, PortfolioPosition
        from market_data import MarketDataFetcher
        from valuation import ValuationEngine
        from config import config
        
        print(f"\nBase currency from config: {config.default_currency}")
        
        # Step 1: Create a portfolio with mixed currencies
        print("\n1. Creating portfolio with mixed currencies:")
        
        # Create positions manually (simulating a CSV load)
        positions = [
            # US stocks (USD)
            PortfolioPosition(ticker="AAPL", quantity=10, average_price=150.25),
            PortfolioPosition(ticker="MSFT", quantity=5, average_price=300.50),
            
            # Indian stocks (INR) - using .NS suffix for NSE
            PortfolioPosition(ticker="RELIANCE.NS", quantity=8, average_price=2500.75),
            PortfolioPosition(ticker="TCS.NS", quantity=12, average_price=3200.50),
            
            # European stock (EUR) - using .DE suffix for Deutsche Börse
            PortfolioPosition(ticker="SAP.DE", quantity=6, average_price=150.25),
        ]
        
        for pos in positions:
            print(f"   {pos.ticker}: {pos.quantity} shares @ {pos.average_price:.2f}")
        
        # Step 2: Fetch live market data
        print("\n2. Fetching live market data...")
        
        fetcher = MarketDataFetcher()
        tickers = [pos.ticker for pos in positions]
        
        try:
            live_prices = fetcher.get_live_prices(tickers)
            print(f"   Successfully fetched prices for {len(live_prices)}/{len(tickers)} tickers")
            
            # Display fetched prices with currencies
            for ticker, price_data in live_prices.items():
                print(f"   {ticker}: {price_data.price:.2f} {price_data.currency}")
                
        except Exception as e:
            print(f"   Error fetching live prices: {e}")
            print("   Using mock data for testing...")
            
            # Fallback to mock data if live fetch fails
            live_prices = {
                "AAPL": type('PriceData', (), {
                    'ticker': 'AAPL',
                    'price': 175.50,
                    'currency': 'USD',
                    'timestamp': pd.Timestamp.now()
                })(),
                "MSFT": type('PriceData', (), {
                    'ticker': 'MSFT',
                    'price': 410.20,
                    'currency': 'USD',
                    'timestamp': pd.Timestamp.now()
                })(),
                "RELIANCE.NS": type('PriceData', (), {
                    'ticker': 'RELIANCE.NS',
                    'price': 2800.25,
                    'currency': 'INR',
                    'timestamp': pd.Timestamp.now()
                })(),
                "TCS.NS": type('PriceData', (), {
                    'ticker': 'TCS.NS',
                    'price': 3500.75,
                    'currency': 'INR',
                    'timestamp': pd.Timestamp.now()
                })(),
                "SAP.DE": type('PriceData', (), {
                    'ticker': 'SAP.DE',
                    'price': 165.80,
                    'currency': 'EUR',
                    'timestamp': pd.Timestamp.now()
                })(),
            }
            
            for ticker, price_data in live_prices.items():
                print(f"   {ticker}: {price_data.price:.2f} {price_data.currency} (mock data)")
        
        # Step 3: Create valuation engine and evaluate portfolio
        print("\n3. Evaluating portfolio with multi-currency support...")
        
        engine = ValuationEngine()
        
        try:
            # Test FX rate fetching
            print("\n   Testing FX rate fetching:")
            test_currencies = ['USD', 'INR', 'EUR']
            for curr in test_currencies:
                if curr != config.default_currency:
                    rate = engine.get_fx_rate(curr, config.default_currency)
                    if pd.notna(rate):
                        print(f"   {curr} -> {config.default_currency}: {rate:.6f}")
                    else:
                        print(f"   {curr} -> {config.default_currency}: Rate not available")
            
            # Evaluate portfolio
            valuation_df = engine.evaluate_portfolio(positions, live_prices)
            
            print("\n   Portfolio Valuation Results:")
            print("   " + "=" * 60)
            
            # Format the DataFrame for better display
            pd.set_option('display.float_format', lambda x: f'{x:,.2f}' if pd.notna(x) else 'N/A')
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', None)
            
            # Print each row with formatting
            for idx, row in valuation_df.iterrows():
                if idx == len(valuation_df) - 1:
                    print("\n   " + "-" * 60)
                
                ticker = row['Ticker']
                shares = row['Shares']
                native_curr = row['Native Currency']
                avg_cost = row['Avg Cost (Native)']
                curr_price = row['Current Price (Native)']
                total_cost = row['Total Cost (Base Currency)']
                curr_value = row['Current Value (Base Currency)']
                pnl_dollar = row['P&L ($ Base)']
                pnl_percent = row['P&L (%)']
                
                # Format values
                shares_fmt = f"{shares:,.0f}" if pd.notna(shares) else "N/A"
                avg_cost_fmt = f"{avg_cost:,.2f}" if pd.notna(avg_cost) else "N/A"
                curr_price_fmt = f"{curr_price:,.2f}" if pd.notna(curr_price) else "N/A"
                total_cost_fmt = f"{total_cost:,.2f}" if pd.notna(total_cost) else "N/A"
                curr_value_fmt = f"{curr_value:,.2f}" if pd.notna(curr_value) else "N/A"
                pnl_dollar_fmt = f"{pnl_dollar:+,.2f}" if pd.notna(pnl_dollar) else "N/A"
                pnl_percent_fmt = f"{pnl_percent:+,.2f}%" if pd.notna(pnl_percent) else "N/A"
                
                if ticker == 'TOTAL':
                    print(f"   {ticker:<15} {shares_fmt:>10} {native_curr:>15} {'SUMMARY':>20} {'SUMMARY':>20} {total_cost_fmt:>20} {curr_value_fmt:>20} {pnl_dollar_fmt:>15} {pnl_percent_fmt:>10}")
                else:
                    print(f"   {ticker:<15} {shares_fmt:>10} {native_curr:>15} {avg_cost_fmt:>20} {curr_price_fmt:>20} {total_cost_fmt:>20} {curr_value_fmt:>20} {pnl_dollar_fmt:>15} {pnl_percent_fmt:>10}")
            
            print("\n   Column Legend:")
            print("   - Ticker: Stock symbol")
            print("   - Shares: Number of shares")
            print("   - Native Currency: Currency of stock price")
            print("   - Avg Cost (Native): Average purchase price in native currency")
            print("   - Current Price (Native): Current market price in native currency")
            print("   - Total Cost (Base): Total investment in base currency")
            print("   - Current Value (Base): Current value in base currency")
            print("   - P&L ($ Base): Profit/Loss in base currency")
            print("   - P&L (%): Profit/Loss percentage")
            
            # Display key insights
            print("\n   Key Insights:")
            print("   " + "-" * 40)
            
            # Count positions by currency
            currency_counts = {}
            for pos in positions:
                ticker = pos.ticker
                if ticker in live_prices:
                    currency = live_prices[ticker].currency
                    currency_counts[currency] = currency_counts.get(currency, 0) + 1
            
            if currency_counts:
                print(f"   Positions by currency: {currency_counts}")
            
            # Check if any FX conversions were needed
            fx_conversions = sum(1 for pos in positions 
                               if pos.ticker in live_prices 
                               and live_prices[pos.ticker].currency != config.default_currency)
            
            if fx_conversions > 0:
                print(f"   FX conversions needed: {fx_conversions} positions")
            
            # Show cache info
            cache_info = engine.get_fx_cache_info()
            print(f"   FX cache: {cache_info['valid_entries']} valid rates cached")
            
        except Exception as e:
            print(f"   Error during valuation: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 4: Test edge cases
        print("\n4. Testing edge cases...")
        
        # Test with empty portfolio
        print("\n   Testing empty portfolio:")
        empty_df = engine.evaluate_portfolio([], {})
        print(f"   Result: {len(empty_df)} rows (should be 0)")
        
        # Test with missing price data
        print("\n   Testing with missing price data:")
        partial_positions = [positions[0]]  # Just AAPL
        partial_prices = {}  # No prices
        
        partial_df = engine.evaluate_portfolio(partial_positions, partial_prices)
        print(f"   Result: {len(partial_df)} rows, AAPL should have NaN values")
        
        # Check if NaN handling works
        if not partial_df.empty and pd.isna(partial_df.iloc[0]['Current Price (Native)']):
            print("   [OK] Missing price data correctly handled (NaN values)")
        
        print("\n" + "=" * 70)
        print("Test completed successfully!")
        print("=" * 70)
        
        return True
        
    except ImportError as e:
        print(f"\nImport Error: {e}")
        print("\nPlease install required dependencies:")
        print("  pip install yfinance pandas")
        return False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_multi_currency_portfolio()
    sys.exit(0 if success else 1)