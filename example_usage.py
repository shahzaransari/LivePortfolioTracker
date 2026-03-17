"""
Example usage of the Portfolio Manager module.
This demonstrates how to use the portfolio_manager.py module in a real application.
"""

import os
from portfolio_manager import PortfolioManager, PortfolioPosition


def demonstrate_basic_usage():
    """Demonstrate basic usage of the Portfolio Manager."""
    print("=" * 60)
    print("Portfolio Manager - Basic Usage Example")
    print("=" * 60)
    
    # Create a portfolio manager
    manager = PortfolioManager()
    
    # Method 1: Add positions manually
    print("\n1. Adding positions manually:")
    positions = [
        PortfolioPosition(ticker="AAPL", quantity=10, average_price=150.25),
        PortfolioPosition(ticker="MSFT", quantity=5, average_price=300.50),
        PortfolioPosition(ticker="GOOGL", quantity=2, average_price=2800.75),
    ]
    
    for pos in positions:
        manager.add_position(pos)
        print(f"  Added: {pos}")
    
    print(f"\n  Portfolio summary:")
    summary = manager.get_portfolio_summary()
    print(f"    Total positions: {summary['total_positions']}")
    print(f"    Total investment: ${summary['total_investment']:.2f}")
    print(f"    Unique tickers: {', '.join(summary['unique_tickers'])}")
    
    # Method 2: Load from CSV
    print("\n2. Loading from CSV file:")
    if os.path.exists("test_portfolio.csv"):
        try:
            # Clear existing positions
            manager = PortfolioManager()
            
            # Load from CSV
            loaded_positions = manager.load_from_csv("test_portfolio.csv")
            print(f"  ✓ Loaded {len(loaded_positions)} positions from test_portfolio.csv")
            
            # Show portfolio
            print(f"\n  Current portfolio:")
            for i, pos in enumerate(manager.positions, 1):
                print(f"    {i}. {pos}")
            
            print(f"\n  Total investment: ${manager.total_investment:.2f}")
            
        except Exception as e:
            print(f"  ✗ Error loading CSV: {e}")
    else:
        print("  ℹ️ test_portfolio.csv not found. Create it with the example format.")
    
    # Demonstrate position operations
    print("\n3. Position operations:")
    
    # Get a position
    aapl_position = manager.get_position("AAPL")
    if aapl_position:
        print(f"  ✓ Found AAPL position: {aapl_position}")
        print(f"    Total cost: ${aapl_position.total_cost:.2f}")
    
    # Try to get non-existent position
    non_existent = manager.get_position("XYZ")
    if non_existent is None:
        print(f"  ✓ XYZ not found (as expected)")
    
    # Remove a position
    removed = manager.remove_position("MSFT")
    if removed:
        print(f"  ✓ Removed MSFT: {removed}")
        print(f"    Updated total positions: {manager.total_positions}")
    
    # Save portfolio to CSV
    print("\n4. Saving portfolio to CSV:")
    try:
        manager.save_to_csv("my_portfolio.csv")
        print(f"  ✓ Saved portfolio to my_portfolio.csv")
        print(f"    Contains {manager.total_positions} positions")
    except Exception as e:
        print(f"  ✗ Error saving: {e}")
    
    return manager


def demonstrate_error_handling():
    """Demonstrate error handling scenarios."""
    print("\n" + "=" * 60)
    print("Portfolio Manager - Error Handling Examples")
    print("=" * 60)
    
    manager = PortfolioManager()
    
    print("\n1. Creating invalid positions:")
    
    # Test invalid quantity
    try:
        invalid_pos = PortfolioPosition(ticker="INVALID", quantity=-5, average_price=100)
        print("  ✗ Should have raised ValueError for negative quantity")
    except ValueError as e:
        print(f"  ✓ Correctly caught: {e}")
    
    # Test invalid price
    try:
        invalid_pos = PortfolioPosition(ticker="INVALID", quantity=10, average_price=0)
        print("  ✗ Should have raised ValueError for zero price")
    except ValueError as e:
        print(f"  ✓ Correctly caught: {e}")
    
    print("\n2. Loading non-existent file:")
    try:
        manager.load_from_csv("does_not_exist.csv")
        print("  ✗ Should have raised FileNotFoundError")
    except FileNotFoundError as e:
        print(f"  ✓ Correctly caught: {e}")
    
    print("\n3. Adding duplicate position:")
    try:
        manager.add_position(PortfolioPosition(ticker="AAPL", quantity=10, average_price=150.25))
        manager.add_position(PortfolioPosition(ticker="AAPL", quantity=5, average_price=200.00))
        print("  ✗ Should have raised ValueError for duplicate ticker")
    except ValueError as e:
        print(f"  ✓ Correctly caught: {e}")


def create_sample_csv_files():
    """Create sample CSV files for demonstration."""
    print("\n" + "=" * 60)
    print("Creating Sample CSV Files")
    print("=" * 60)
    
    # Create a simple portfolio CSV
    sample_content = """Ticker,Quantity,AveragePrice
AAPL,10,150.25
MSFT,5,300.50
GOOGL,2,2800.75
TSLA,15,200.30
NVDA,8,450.75
AMZN,3,3500.00
"""
    
    with open("sample_portfolio.csv", "w") as f:
        f.write(sample_content)
    
    print("✓ Created sample_portfolio.csv with 6 positions")
    
    # Create a CSV with mixed case tickers
    mixed_case_content = """Ticker,Quantity,AveragePrice
aapl,10,150.25
MsFt,5,300.50
googl,2,2800.75
TsLa,15,200.30
"""
    
    with open("mixed_case_portfolio.csv", "w") as f:
        f.write(mixed_case_content)
    
    print("✓ Created mixed_case_portfolio.csv (demonstrates case conversion)")
    
    return ["sample_portfolio.csv", "mixed_case_portfolio.csv"]


def main():
    """Main demonstration function."""
    print("Live Portfolio Tracker - Portfolio Manager Demo")
    print("=" * 60)
    
    # Create sample files
    sample_files = create_sample_csv_files()
    
    # Demonstrate basic usage
    manager = demonstrate_basic_usage()
    
    # Demonstrate error handling
    demonstrate_error_handling()
    
    # Demonstrate loading from sample files
    print("\n" + "=" * 60)
    print("Loading from Sample Files")
    print("=" * 60)
    
    for filename in sample_files:
        if os.path.exists(filename):
            try:
                test_manager = PortfolioManager()
                positions = test_manager.load_from_csv(filename)
                print(f"\n✓ Loaded {len(positions)} positions from {filename}")
                print(f"  Total investment: ${test_manager.total_investment:.2f}")
                
                # Show first 3 positions
                print("  First 3 positions:")
                for i, pos in enumerate(positions[:3], 1):
                    print(f"    {i}. {pos}")
                
            except Exception as e:
                print(f"\n✗ Error loading {filename}: {e}")
    
    print("\n" + "=" * 60)
    print("Integration with Existing Config Module")
    print("=" * 60)
    
    # Show how it integrates with the existing config module
    try:
        from config import config
        print(f"\n✓ Successfully imported config module")
        print(f"  Environment: {config.environment}")
        print(f"  Debug mode: {config.debug_mode}")
        print(f"  Default currency: {config.default_currency}")
        
        # Example: Use config settings in portfolio manager
        print(f"\n  Portfolio Manager logging level: {'DEBUG' if config.debug_mode else 'INFO'}")
        
    except ImportError:
        print("\nℹ️ Config module not available (running standalone)")
    
    print("\n" + "=" * 60)
    print("Demo Completed Successfully!")
    print("=" * 60)
    
    print("\nFiles created:")
    print("  - portfolio_manager.py (main module)")
    print("  - test_portfolio.csv (sample data)")
    print("  - sample_portfolio.csv (demo data)")
    print("  - mixed_case_portfolio.csv (demo data)")
    print("  - my_portfolio.csv (saved portfolio)")
    print("\nNext steps:")
    print("  1. Review portfolio_manager.py for implementation details")
    print("  2. Use PortfolioManager() to create portfolio instances")
    print("  3. Call load_from_csv('your_file.csv') to load data")
    print("  4. Use get_position(), add_position(), remove_position() methods")
    print("  5. Call save_to_csv() to save your portfolio")
    
    return manager


if __name__ == "__main__":
    main()