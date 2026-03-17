"""
Module 2: Portfolio Data Handler for Live Portfolio Tracker

This module handles reading, storing, and managing portfolio positions from CSV files.
It provides a clean interface for loading and validating portfolio data.

Example portfolio.csv file structure:
----------------------------------------
Ticker,Quantity,AveragePrice
AAPL,10,150.25
MSFT,5,300.50
GOOGL,2,2800.75
TSLA,15,200.30
----------------------------------------

Note: Headers are case-sensitive and should be exactly as shown above.
"""

import csv
import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

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
class PortfolioPosition:
    """
    Data class representing a single portfolio holding.
    
    Attributes:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        quantity (float): Number of shares held
        average_price (float): Average purchase price per share
        
    Note:
        - Ticker is automatically converted to uppercase
        - Quantity and average_price must be positive numbers
    """
    
    ticker: str
    quantity: float
    average_price: float
    
    def __post_init__(self):
        """Post-initialization validation and formatting."""
        # Convert ticker to uppercase
        self.ticker = self.ticker.upper().strip()
        
        # Validate numeric values
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive, got {self.quantity}")
        if self.average_price <= 0:
            raise ValueError(f"Average price must be positive, got {self.average_price}")
    
    @property
    def total_cost(self) -> float:
        """Calculate total cost of this position."""
        return self.quantity * self.average_price
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert position to dictionary representation."""
        return {
            'ticker': self.ticker,
            'quantity': self.quantity,
            'average_price': self.average_price,
            'total_cost': self.total_cost
        }
    
    def __str__(self) -> str:
        """String representation of the position."""
        return f"{self.ticker}: {self.quantity} shares @ ${self.average_price:.2f}"


class PortfolioManager:
    """
    Manager class for handling portfolio positions.
    
    This class provides methods to load, store, and manage portfolio positions
    from CSV files with proper validation and error handling.
    
    Attributes:
        positions (List[PortfolioPosition]): List of portfolio positions
        total_positions (int): Total number of positions
        total_investment (float): Total investment across all positions
    """
    
    # Expected CSV headers
    EXPECTED_HEADERS = ['Ticker', 'Quantity', 'AveragePrice']
    
    def __init__(self):
        """Initialize an empty portfolio manager."""
        self.positions: List[PortfolioPosition] = []
        self._position_dict: Dict[str, PortfolioPosition] = {}
        self.total_positions: int = 0
        self.total_investment: float = 0.0
        
        logger.debug("PortfolioManager initialized")
    
    def load_from_csv(self, filepath: str) -> List[PortfolioPosition]:
        """
        Load portfolio positions from a CSV file.
        
        Args:
            filepath: Path to the CSV file containing portfolio data
            
        Returns:
            List[PortfolioPosition]: List of loaded portfolio positions
            
        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            ValueError: If the CSV contains invalid data or format
            PermissionError: If the file cannot be read due to permissions
            csv.Error: If there are CSV parsing errors
            
        Example:
            >>> manager = PortfolioManager()
            >>> positions = manager.load_from_csv('portfolio.csv')
            >>> print(f"Loaded {len(positions)} positions")
        """
        filepath_obj = Path(filepath)
        
        # Check if file exists
        if not filepath_obj.exists():
            error_msg = f"Portfolio CSV file not found: {filepath}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Check if file is readable
        if not filepath_obj.is_file():
            error_msg = f"Path is not a file: {filepath}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Loading portfolio from CSV: {filepath}")
        
        try:
            with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
                # Use DictReader for header-based access
                reader = csv.DictReader(csvfile)
                
                # Validate headers
                if reader.fieldnames is None:
                    raise ValueError("CSV file appears to be empty or has no headers")
                
                missing_headers = [h for h in self.EXPECTED_HEADERS if h not in reader.fieldnames]
                if missing_headers:
                    error_msg = f"Missing required headers in CSV: {missing_headers}. Expected: {self.EXPECTED_HEADERS}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                # Process each row
                loaded_positions = []
                row_num = 1  # Start from 1 (header is row 0)
                
                for row in reader:
                    row_num += 1
                    
                    try:
                        # Extract and validate data
                        ticker = row['Ticker'].strip()
                        if not ticker:
                            raise ValueError(f"Row {row_num}: Ticker cannot be empty")
                        
                        # Parse quantity
                        try:
                            quantity = float(row['Quantity'])
                        except ValueError:
                            raise ValueError(
                                f"Row {row_num}: Invalid quantity '{row['Quantity']}'. "
                                "Must be a number."
                            )
                        
                        # Parse average price
                        try:
                            average_price = float(row['AveragePrice'])
                        except ValueError:
                            raise ValueError(
                                f"Row {row_num}: Invalid average price '{row['AveragePrice']}'. "
                                "Must be a number."
                            )
                        
                        # Create position (validation happens in __post_init__)
                        position = PortfolioPosition(
                            ticker=ticker,
                            quantity=quantity,
                            average_price=average_price
                        )
                        
                        loaded_positions.append(position)
                        logger.debug(f"Loaded position: {position}")
                        
                    except ValueError as e:
                        logger.error(f"Error in row {row_num}: {e}")
                        # Re-raise with more context
                        raise ValueError(f"CSV parsing error at row {row_num}: {e}")
                
                # Update internal state
                self.positions = loaded_positions
                self._update_internal_state()
                
                logger.info(f"Successfully loaded {len(loaded_positions)} positions from {filepath}")
                return loaded_positions
                
        except PermissionError as e:
            error_msg = f"Permission denied when reading file: {filepath}"
            logger.error(error_msg)
            raise PermissionError(error_msg) from e
        except csv.Error as e:
            error_msg = f"CSV parsing error in file {filepath}: {e}"
            logger.error(error_msg)
            raise csv.Error(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error loading CSV file {filepath}: {e}"
            logger.error(error_msg)
            raise
    
    def _update_internal_state(self) -> None:
        """Update internal state after positions change."""
        # Update position dictionary for quick lookup
        self._position_dict = {pos.ticker: pos for pos in self.positions}
        
        # Update totals
        self.total_positions = len(self.positions)
        self.total_investment = sum(pos.total_cost for pos in self.positions)
        
        logger.debug(f"Updated internal state: {self.total_positions} positions, "
                    f"${self.total_investment:.2f} total investment")
    
    def get_position(self, ticker: str) -> Optional[PortfolioPosition]:
        """
        Get a position by ticker symbol.
        
        Args:
            ticker: Stock ticker symbol (case-insensitive)
            
        Returns:
            PortfolioPosition if found, None otherwise
        """
        ticker_upper = ticker.upper()
        return self._position_dict.get(ticker_upper)
    
    def add_position(self, position: PortfolioPosition) -> None:
        """
        Add a new position to the portfolio.
        
        Args:
            position: PortfolioPosition to add
            
        Raises:
            ValueError: If position with same ticker already exists
        """
        if position.ticker in self._position_dict:
            raise ValueError(f"Position with ticker {position.ticker} already exists")
        
        self.positions.append(position)
        self._update_internal_state()
        logger.info(f"Added position: {position}")
    
    def remove_position(self, ticker: str) -> Optional[PortfolioPosition]:
        """
        Remove a position by ticker symbol.
        
        Args:
            ticker: Stock ticker symbol (case-insensitive)
            
        Returns:
            Removed PortfolioPosition if found, None otherwise
        """
        ticker_upper = ticker.upper()
        
        for i, position in enumerate(self.positions):
            if position.ticker == ticker_upper:
                removed = self.positions.pop(i)
                self._update_internal_state()
                logger.info(f"Removed position: {removed}")
                return removed
        
        logger.warning(f"Position with ticker {ticker_upper} not found")
        return None
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the portfolio.
        
        Returns:
            Dictionary with portfolio summary information
        """
        return {
            'total_positions': self.total_positions,
            'total_investment': self.total_investment,
            'positions': [pos.to_dict() for pos in self.positions],
            'unique_tickers': list(self._position_dict.keys())
        }
    
    def save_to_csv(self, filepath: str) -> None:
        """
        Save portfolio positions to a CSV file.
        
        Args:
            filepath: Path where to save the CSV file
            
        Raises:
            PermissionError: If the file cannot be written
        """
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.EXPECTED_HEADERS)
                writer.writeheader()
                
                for position in self.positions:
                    writer.writerow({
                        'Ticker': position.ticker,
                        'Quantity': position.quantity,
                        'AveragePrice': position.average_price
                    })
            
            logger.info(f"Saved {len(self.positions)} positions to {filepath}")
            
        except PermissionError as e:
            error_msg = f"Permission denied when writing to file: {filepath}"
            logger.error(error_msg)
            raise PermissionError(error_msg) from e
        except Exception as e:
            error_msg = f"Error saving to CSV file {filepath}: {e}"
            logger.error(error_msg)
            raise
    
    def __str__(self) -> str:
        """String representation of the portfolio manager."""
        if not self.positions:
            return "PortfolioManager (empty)"
        
        positions_str = "\n  ".join(str(pos) for pos in self.positions)
        return (f"PortfolioManager with {self.total_positions} positions "
                f"(Total investment: ${self.total_investment:.2f}):\n  {positions_str}")


# Example usage and testing
if __name__ == "__main__":
    print("=" * 60)
    print("Portfolio Manager Module - Test")
    print("=" * 60)
    
    # Create a portfolio manager
    manager = PortfolioManager()
    
    # Example 1: Create positions manually
    print("\n1. Creating positions manually:")
    positions = [
        PortfolioPosition(ticker="AAPL", quantity=10, average_price=150.25),
        PortfolioPosition(ticker="MSFT", quantity=5, average_price=300.50),
        PortfolioPosition(ticker="GOOGL", quantity=2, average_price=2800.75),
    ]
    
    for pos in positions:
        try:
            manager.add_position(pos)
            print(f"  Added: {pos}")
        except ValueError as e:
            print(f"  Error: {e}")
    
    print(f"\n  Portfolio summary: {manager.get_portfolio_summary()}")
    
    # Example 2: Get position by ticker
    print("\n2. Getting position by ticker:")
    aapl_position = manager.get_position("AAPL")
    if aapl_position:
        print(f"  Found AAPL: {aapl_position}")
        print(f"  Total cost: ${aapl_position.total_cost:.2f}")
    
    # Example 3: Remove a position
    print("\n3. Removing a position:")
    removed = manager.remove_position("MSFT")
    if removed:
        print(f"  Removed: {removed}")
    
    print(f"\n  Updated portfolio: {manager}")
    
    # Example 4: Save to CSV
    print("\n4. Saving to CSV (example):")
    try:
        manager.save_to_csv("example_portfolio.csv")
        print("  Saved to example_portfolio.csv")
    except Exception as e:
        print(f"  Error saving: {e}")
    
    # Example 5: Load from CSV (simulated)
    print("\n5. Simulating CSV load:")
    print("  To test CSV loading, create a file 'portfolio.csv' with format:")
    print("  Ticker,Quantity,AveragePrice")
    print("  AAPL,10,150.25")
    print("  MSFT,5,300.50")
    print("  GOOGL,2,2800.75")
    print("\n  Then run: manager.load_from_csv('portfolio.csv')")
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)