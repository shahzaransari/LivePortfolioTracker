"""
Module 5: Main Execution & Display for Live Portfolio Tracker

This module provides a beautiful, live-updating terminal interface for the portfolio tracker.
It integrates all components (PortfolioManager, MarketDataFetcher, ValuationEngine) into a
real-time monitoring application with rich visual display.

Requirements:
    pip install rich pandas yfinance

Features:
    - Live portfolio valuation with automatic refresh
    - Beautiful terminal display using rich library
    - Color-coded P&L (green for positive, red for negative)
    - Cross-platform terminal clearing
    - Automatic dummy portfolio creation if portfolio.csv doesn't exist
    - Graceful exit with Ctrl+C

Usage:
    python main.py

Note:
    - Press Ctrl+C to stop the tracker
    - Edit portfolio.csv to customize your holdings
    - Configure refresh interval in config.py or .env file
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Import required libraries
try:
    import pandas as pd
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.text import Text
    from rich.panel import Panel
    from rich.layout import Layout
    from rich import box
except ImportError as e:
    print(f"Error: Required library not found: {e}")
    print("Please install required libraries with:")
    print("  pip install rich pandas yfinance")
    sys.exit(1)

# Import our custom modules
try:
    from config import config
    from portfolio_manager import PortfolioManager, PortfolioPosition
    from market_data import MarketDataFetcher, PriceData
    from valuation import ValuationEngine
except ImportError as e:
    print(f"Error: Could not import portfolio tracker modules: {e}")
    print("Make sure all required modules (config.py, portfolio_manager.py, etc.) are in the same directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.debug_mode else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global console for rich output
console = Console()


def clear_terminal() -> None:
    """
    Clear the terminal screen in a cross-platform way.
    
    Works on Windows (cls) and Unix-like systems (clear).
    """
    os.system('cls' if os.name == 'nt' else 'clear')


def create_dummy_portfolio(filepath: str = "portfolio.csv") -> None:
    """
    Create a dummy portfolio CSV file if it doesn't exist.
    
    This ensures users see the tracker working immediately without
    having to create their own portfolio file first.
    
    Args:
        filepath: Path to the portfolio CSV file
    """
    if os.path.exists(filepath):
        logger.info(f"Portfolio file already exists: {filepath}")
        return
    
    logger.info(f"Creating dummy portfolio file: {filepath}")
    
    # Create a diverse dummy portfolio with global stocks
    dummy_portfolio = """Ticker,Quantity,AveragePrice
AAPL,10,150.25
MSFT,5,300.50
RELIANCE.NS,20,2500.75
SAP.DE,8,150.30
TSLA,15,200.40
GOOGL,2,2800.00
AMZN,3,3500.25
NVDA,8,450.50
"""
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(dummy_portfolio)
        logger.info(f"Created dummy portfolio with 8 global stocks")
        
        # Also create a README note
        readme_note = f"""
# Live Portfolio Tracker - Dummy Portfolio
# -----------------------------------------
# This file was automatically created because no portfolio.csv was found.
# You can edit this file with your own holdings.
# 
# Format: Ticker,Quantity,AveragePrice
# Example: AAPL,10,150.25
# 
# Current dummy holdings:
# - AAPL (Apple Inc.) - US stock
# - MSFT (Microsoft) - US stock  
# - RELIANCE.NS (Reliance Industries) - Indian stock
# - SAP.DE (SAP SE) - German stock
# - TSLA (Tesla) - US stock
# - GOOGL (Alphabet) - US stock
# - AMZN (Amazon) - US stock
# - NVDA (NVIDIA) - US stock
"""
        with open(filepath + ".README.txt", 'w', encoding='utf-8') as f:
            f.write(readme_note)
            
    except Exception as e:
        logger.error(f"Failed to create dummy portfolio: {e}")
        raise


def display_portfolio(df: pd.DataFrame) -> None:
    """
    Display portfolio valuation DataFrame using rich.table.
    
    Creates a beautiful, formatted table with color-coded P&L values
    and proper currency formatting.
    
    Args:
        df: Portfolio valuation DataFrame from ValuationEngine
    """
    if df.empty:
        console.print("[bold red]No portfolio data to display[/bold red]")
        return
    
    # Create the main table
    table = Table(
        title="[bold cyan]Live Portfolio Valuation[/bold cyan]",
        box=box.ROUNDED,
        header_style="bold magenta",
        title_style="bold cyan",
        show_header=True,
        show_footer=True,
        expand=True
    )
    
    # Define columns with appropriate formatting
    columns = [
        ("Ticker", "left", "bold"),
        ("Shares", "right", "dim"),
        ("Currency", "center", "dim"),
        ("Avg Cost", "right", "dim"),
        ("Curr Price", "right", "bold"),
        ("Total Cost", "right", "dim cyan"),
        ("Curr Value", "right", "dim green"),
        ("P&L ($)", "right", None),  # Style determined by value
        ("P&L (%)", "right", None),  # Style determined by value
    ]
    
    # Add columns to table
    for col_name, justify, style in columns:
        table.add_column(col_name, justify=justify, style=style)
    
    # Add data rows
    for _, row in df.iterrows():
        ticker = str(row['Ticker'])
        
        # Skip the TOTAL row for now (we'll add it separately)
        if ticker == 'TOTAL':
            continue
        
        # Format values
        shares = f"{row['Shares']:.2f}" if not pd.isna(row['Shares']) else "N/A"
        currency = str(row['Native Currency']) if not pd.isna(row['Native Currency']) else "N/A"
        avg_cost = f"{row['Avg Cost (Native)']:.2f}" if not pd.isna(row['Avg Cost (Native)']) else "N/A"
        curr_price = f"{row['Current Price (Native)']:.2f}" if not pd.isna(row['Current Price (Native)']) else "N/A"
        
        # Format currency values with 2 decimal places
        total_cost = f"${row['Total Cost (Base Currency)']:.2f}" if not pd.isna(row['Total Cost (Base Currency)']) else "N/A"
        curr_value = f"${row['Current Value (Base Currency)']:.2f}" if not pd.isna(row['Current Value (Base Currency)']) else "N/A"
        
        # Format P&L with color coding
        pnl_dollar = row['P&L ($ Base)']
        pnl_percent = row['P&L (%)']
        
        if pd.isna(pnl_dollar):
            pnl_dollar_str = "N/A"
            pnl_percent_str = "N/A"
        else:
            # Color code based on value
            if pnl_dollar >= 0:
                pnl_dollar_str = f"[green]${pnl_dollar:+.2f}[/green]"
                pnl_percent_str = f"[green]{pnl_percent:+.2f}%[/green]" if not pd.isna(pnl_percent) else "N/A"
            else:
                pnl_dollar_str = f"[red]${pnl_dollar:+.2f}[/red]"
                pnl_percent_str = f"[red]{pnl_percent:+.2f}%[/red]" if not pd.isna(pnl_percent) else "N/A"
        
        # Add row to table
        table.add_row(
            ticker, shares, currency, avg_cost, curr_price,
            total_cost, curr_value, pnl_dollar_str, pnl_percent_str
        )
    
    # Add separator before total row
    table.add_row(*["-" * 8 for _ in range(9)], style="dim")
    
    # Add total row (if present)
    total_row = df[df['Ticker'] == 'TOTAL']
    if not total_row.empty:
        total = total_row.iloc[0]
        
        # Format total values
        total_shares = f"{total['Shares']:.2f}" if not pd.isna(total['Shares']) else "N/A"
        total_cost_val = f"${total['Total Cost (Base Currency)']:.2f}" if not pd.isna(total['Total Cost (Base Currency)']) else "N/A"
        total_value_val = f"${total['Current Value (Base Currency)']:.2f}" if not pd.isna(total['Current Value (Base Currency)']) else "N/A"
        
        # Format total P&L
        total_pnl_dollar = total['P&L ($ Base)']
        total_pnl_percent = total['P&L (%)']
        
        if pd.isna(total_pnl_dollar):
            total_pnl_dollar_str = "N/A"
            total_pnl_percent_str = "N/A"
        else:
            if total_pnl_dollar >= 0:
                total_pnl_dollar_str = f"[bold green]${total_pnl_dollar:+.2f}[/bold green]"
                total_pnl_percent_str = f"[bold green]{total_pnl_percent:+.2f}%[/bold green]" if not pd.isna(total_pnl_percent) else "N/A"
            else:
                total_pnl_dollar_str = f"[bold red]${total_pnl_dollar:+.2f}[/bold red]"
                total_pnl_percent_str = f"[bold red]{total_pnl_percent:+.2f}%[/bold red]" if not pd.isna(total_pnl_percent) else "N/A"
        
        # Add total row with bold styling
        table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{total_shares}[/bold]",
            "[bold]MULTI[/bold]",
            "[bold]-[/bold]",
            "[bold]-[/bold]",
            f"[bold]{total_cost_val}[/bold]",
            f"[bold]{total_value_val}[/bold]",
            total_pnl_dollar_str,
            total_pnl_percent_str,
            style="bold"
        )
    
    # Display the table
    console.print(table)
    
    # Add timestamp and refresh info
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    refresh_info = f"Last updated: {current_time} | Next refresh in: {config.refresh_interval_seconds}s"
    console.print(f"\n[dim]{refresh_info}[/dim]")
    console.print("[dim]Press Ctrl+C to stop the tracker[/dim]")


def get_portfolio_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary statistics from the portfolio DataFrame.
    
    Args:
        df: Portfolio valuation DataFrame
        
    Returns:
        Dictionary with summary statistics
    """
    if df.empty:
        return {}
    
    # Get total row
    total_row = df[df['Ticker'] == 'TOTAL']
    if total_row.empty:
        return {}
    
    total = total_row.iloc[0]
    
    # Calculate additional stats
    total_cost = total['Total Cost (Base Currency)']
    total_value = total['Current Value (Base Currency)']
    total_pnl_dollar = total['P&L ($ Base)']
    total_pnl_percent = total['P&L (%)']
    
    # Count winning and losing positions
    winning_positions = 0
    losing_positions = 0
    neutral_positions = 0
    
    for _, row in df.iterrows():
        if row['Ticker'] == 'TOTAL':
            continue
        
        pnl = row['P&L ($ Base)']
        if pd.isna(pnl):
            neutral_positions += 1
        elif pnl > 0:
            winning_positions += 1
        elif pnl < 0:
            losing_positions += 1
        else:
            neutral_positions += 1
    
    return {
        'total_positions': len(df) - 1,  # Exclude TOTAL row
        'winning_positions': winning_positions,
        'losing_positions': losing_positions,
        'neutral_positions': neutral_positions,
        'total_investment': total_cost,
        'current_value': total_value,
        'total_pnl_dollar': total_pnl_dollar,
        'total_pnl_percent': total_pnl_percent,
        'last_update': datetime.now().isoformat()
    }


def display_summary_panel(stats: Dict[str, Any]) -> None:
    """
    Display a summary panel with key portfolio metrics.
    
    Args:
        stats: Portfolio summary statistics
    """
    if not stats:
        return
    
    # Create summary text
    summary_text = Text()
    
    # Add key metrics
    summary_text.append(f"Total Positions: {stats['total_positions']}\n", style="bold")
    summary_text.append(f"Winning: {stats['winning_positions']} | ", style="green")
    summary_text.append(f"Losing: {stats['losing_positions']} | ", style="red")
    summary_text.append(f"Neutral: {stats['neutral_positions']}\n\n", style="dim")
    
    # Add investment metrics
    total_investment = stats['total_investment']
    current_value = stats['current_value']
    total_pnl_dollar = stats['total_pnl_dollar']
    total_pnl_percent = stats['total_pnl_percent']
    
    if not pd.isna(total_investment):
        summary_text.append(f"Total Investment: ${total_investment:.2f}\n", style="cyan")
    
    if not pd.isna(current_value):
        summary_text.append(f"Current Value: ${current_value:.2f}\n", style="green")
    
    if not pd.isna(total_pnl_dollar):
        if total_pnl_dollar >= 0:
            summary_text.append(f"Total P&L: ${total_pnl_dollar:+.2f} ", style="bold green")
            summary_text.append(f"({total_pnl_percent:+.2f}%)\n", style="green")
        else:
            summary_text.append(f"Total P&L: ${total_pnl_dollar:+.2f} ", style="bold red")
            summary_text.append(f"({total_pnl_percent:+.2f}%)\n", style="red")
    
    # Create and display panel
    panel = Panel(
        summary_text,
        title="[bold]Portfolio Summary[/bold]",
        border_style="cyan",
        padding=(1, 2)
    )
    
    console.print(panel)


def main() -> None:
    """
    Main execution function for the live portfolio tracker.
    
    This function:
    1. Initializes all managers/engines
    2. Creates dummy portfolio if needed
    3. Enters a live update loop
    4. Displays portfolio with rich formatting
    5. Handles graceful exit with Ctrl+C
    """
    logger.info("Starting Live Portfolio Tracker")
    
    # Display welcome message
    console.print(Panel.fit(
        "[bold cyan]Live Portfolio Tracker[/bold cyan]\n"
        "[dim]Real-time portfolio valuation with live market data[/dim]",
        border_style="cyan"
    ))
    
    # Check for required libraries
    try:
        import yfinance
        logger.info("yfinance library available")
    except ImportError:
        console.print("[bold red]Error: yfinance library not installed[/bold red]")
        console.print("Please install it with: [bold]pip install yfinance[/bold]")
        sys.exit(1)
    
    # Initialize managers and engines
    console.print("[dim]Initializing components...[/dim]")
    
    portfolio_manager = PortfolioManager()
    market_data_fetcher = MarketDataFetcher()
    valuation_engine = ValuationEngine()
    
    console.print("[green][OK][/green] Portfolio Manager initialized")
    console.print("[green][OK][/green] Market Data Fetcher initialized")
    console.print("[green][OK][/green] Valuation Engine initialized")
    
    # Create dummy portfolio if needed
    portfolio_file = "portfolio.csv"
    create_dummy_portfolio(portfolio_file)
    
    # Main loop
    console.print(f"\n[bold]Loading portfolio from: {portfolio_file}[/bold]")
    console.print("[dim]Starting live tracker... (Press Ctrl+C to stop)[/dim]\n")
    
    iteration = 0
    last_error = None
    
    try:
        while True:
            iteration += 1
            logger.debug(f"Starting iteration {iteration}")
            
            try:
                # Step A: Clear terminal
                clear_terminal()
                
                # Step B: Print header
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                console.print(f"[bold cyan]Live Portfolio Tracker[/bold cyan] | [dim]{current_time}[/dim]")
                console.print("[dim]" + "-" * 60 + "[/dim]\n")
                
                # Step C: Load portfolio
                try:
                    positions = portfolio_manager.load_from_csv(portfolio_file)
                    logger.info(f"Loaded {len(positions)} positions from {portfolio_file}")
                except Exception as e:
                    logger.error(f"Failed to load portfolio: {e}")
                    console.print(f"[bold red]Error loading portfolio: {e}[/bold red]")
                    console.print("[dim]Check that portfolio.csv exists and has correct format[/dim]")
                    
                    # Show example format
                    console.print("\n[bold]Example portfolio.csv format:[/bold]")
                    console.print("[dim]Ticker,Quantity,AveragePrice")
                    console.print("AAPL,10,150.25")
                    console.print("MSFT,5,300.50")
                    console.print("GOOGL,2,2800.75[/dim]")
                    
                    # Wait before retry
                    time.sleep(config.refresh_interval_seconds)
                    continue
                
                # Step D: Fetch live prices
                tickers = [pos.ticker for pos in positions]
                console.print(f"[dim]Fetching live prices for {len(tickers)} tickers...[/dim]")
                
                try:
                    live_prices = market_data_fetcher.get_live_prices(tickers)
                    logger.info(f"Fetched prices for {len(live_prices)}/{len(tickers)} tickers")
                    
                    if len(live_prices) < len(tickers):
                        missing = set(tickers) - set(live_prices.keys())
                        console.print(f"[yellow]Warning: Could not fetch prices for {len(missing)} tickers[/yellow]")
                        for missing_ticker in list(missing)[:5]:  # Show first 5
                            console.print(f"[dim]  - {missing_ticker}[/dim]")
                        if len(missing) > 5:
                            console.print(f"[dim]  ... and {len(missing) - 5} more[/dim]")
                
                except Exception as e:
                    logger.error(f"Failed to fetch market data: {e}")
                    console.print(f"[bold red]Error fetching market data: {e}[/bold red]")
                    console.print("[dim]Check your internet connection and try again[/dim]")
                    
                    # Use cached prices if available
                    cache_info = market_data_fetcher.get_cache_info()
                    if cache_info['valid_entries'] > 0:
                        console.print(f"[yellow]Using cached prices ({cache_info['valid_entries']} entries)[/yellow]")
                        # Get cached prices
                        cached_prices = {}
                        for ticker in tickers:
                            if ticker in market_data_fetcher._cache:
                                price_data, cache_time = market_data_fetcher._cache[ticker]
                                if time.time() - cache_time < market_data_fetcher.config.cache_ttl_seconds:
                                    cached_prices[ticker] = price_data
                        live_prices = cached_prices
                    else:
                        # No cached data, skip this iteration
                        time.sleep(config.refresh_interval_seconds)
                        continue
                
                # Step E: Evaluate portfolio
                console.print("[dim]Evaluating portfolio...[/dim]")
                
                try:
                    valuation_df = valuation_engine.evaluate_portfolio(positions, live_prices)
                    
                    if valuation_df.empty:
                        console.print("[yellow]No valuation data available[/yellow]")
                    else:
                        # Step F: Display portfolio
                        display_portfolio(valuation_df)
                        
                        # Display summary panel
                        stats = get_portfolio_summary_stats(valuation_df)
                        if stats:
                            console.print()  # Add spacing
                            display_summary_panel(stats)
                
                except Exception as e:
                    logger.error(f"Failed to evaluate portfolio: {e}")
                    console.print(f"[bold red]Error evaluating portfolio: {e}[/bold red]")
                
                # Clear any previous error
                last_error = None
                
            except Exception as e:
                # Catch any unexpected errors in the main loop
                logger.error(f"Unexpected error in main loop: {e}")
                
                # Don't spam the same error
                if str(e) != last_error:
                    console.print(f"[bold red]Unexpected error: {e}[/bold red]")
                    last_error = str(e)
            
            # Step G: Sleep before next refresh
            logger.debug(f"Sleeping for {config.refresh_interval_seconds} seconds")
            
            # Show countdown
            for remaining in range(config.refresh_interval_seconds, 0, -1):
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    raise  # Re-raise to be caught by outer try-except
            
    except KeyboardInterrupt:
        # Graceful exit
        console.print("\n\n[bold yellow]Stopping Live Portfolio Tracker...[/bold yellow]")
        logger.info("Portfolio tracker stopped by user")
        
        # Show final message
        console.print("[green][OK][/green] Tracker stopped gracefully")
        console.print("[dim]Thank you for using Live Portfolio Tracker![/dim]")
        
    except Exception as e:
        # Unexpected error
        logger.error(f"Fatal error in main: {e}")
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]")
        console.print("[dim]Please check the logs for details[/dim]")
        
    finally:
        # Cleanup
        logger.info("Live Portfolio Tracker shutdown complete")


if __name__ == "__main__":
    # Entry point
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted during startup[/dim]")
    except Exception as e:
        console.print(f"[bold red]Fatal startup error: {e}[/bold red]")
        logger.exception("Fatal startup error")