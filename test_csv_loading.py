"""
Test script for Portfolio Manager CSV loading functionality.
This script tests various scenarios including successful loading and error handling.
"""

import os
import tempfile
from portfolio_manager import PortfolioManager, PortfolioPosition


def test_successful_csv_loading():
    """Test successful loading of a valid CSV file."""
    print("=" * 60)
    print("Test 1: Successful CSV Loading")
    print("=" * 60)
    
    manager = PortfolioManager()
    
    try:
        positions = manager.load_from_csv("test_portfolio.csv")
        print(f"✓ Successfully loaded {len(positions)} positions")
        
        # Verify positions
        for i, pos in enumerate(positions, 1):
            print(f"  {i}. {pos}")
        
        # Verify totals
        print(f"\n  Total positions: {manager.total_positions}")
        print(f"  Total investment: ${manager.total_investment:.2f}")
        
        # Test position lookup
        aapl = manager.get_position("aapl")  # Test case-insensitive
        if aapl:
            print(f"\n  Found AAPL (case-insensitive): {aapl}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_file_not_found():
    """Test handling of non-existent file."""
    print("\n" + "=" * 60)
    print("Test 2: File Not Found Error")
    print("=" * 60)
    
    manager = PortfolioManager()
    
    try:
        positions = manager.load_from_csv("non_existent_file.csv")
        print("✗ Should have raised FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"✓ Correctly raised FileNotFoundError: {e}")
        return True
    except Exception as e:
        print(f"✗ Wrong exception type: {type(e).__name__}: {e}")
        return False


def test_invalid_csv_format():
    """Test handling of CSV with invalid format."""
    print("\n" + "=" * 60)
    print("Test 3: Invalid CSV Format")
    print("=" * 60)
    
    # Create a temporary CSV with wrong headers
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("Symbol,Shares,Price\n")
        f.write("AAPL,10,150.25\n")
        temp_file = f.name
    
    manager = PortfolioManager()
    
    try:
        positions = manager.load_from_csv(temp_file)
        print("✗ Should have raised ValueError for wrong headers")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
        return True
    except Exception as e:
        print(f"✗ Wrong exception type: {type(e).__name__}: {e}")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_invalid_numeric_data():
    """Test handling of CSV with invalid numeric data."""
    print("\n" + "=" * 60)
    print("Test 4: Invalid Numeric Data")
    print("=" * 60)
    
    # Create a temporary CSV with invalid numeric data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("Ticker,Quantity,AveragePrice\n")
        f.write("AAPL,ten,150.25\n")  # Invalid quantity
        f.write("MSFT,5,three_hundred\n")  # Invalid price
        temp_file = f.name
    
    manager = PortfolioManager()
    
    try:
        positions = manager.load_from_csv(temp_file)
        print("✗ Should have raised ValueError for invalid numeric data")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
        return True
    except Exception as e:
        print(f"✗ Wrong exception type: {type(e).__name__}: {e}")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_empty_ticker():
    """Test handling of CSV with empty ticker."""
    print("\n" + "=" * 60)
    print("Test 5: Empty Ticker")
    print("=" * 60)
    
    # Create a temporary CSV with empty ticker
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("Ticker,Quantity,AveragePrice\n")
        f.write(",10,150.25\n")  # Empty ticker
        temp_file = f.name
    
    manager = PortfolioManager()
    
    try:
        positions = manager.load_from_csv(temp_file)
        print("✗ Should have raised ValueError for empty ticker")
        return False
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
        return True
    except Exception as e:
        print(f"✗ Wrong exception type: {type(e).__name__}: {e}")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_case_insensitive_ticker():
    """Test that tickers are converted to uppercase."""
    print("\n" + "=" * 60)
    print("Test 6: Case Insensitive Ticker Conversion")
    print("=" * 60)
    
    # Create a temporary CSV with mixed case tickers
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("Ticker,Quantity,AveragePrice\n")
        f.write("aapl,10,150.25\n")  # lowercase
        f.write("MsFt,5,300.50\n")   # mixed case
        f.write("GOOGL,2,2800.75\n") # uppercase
        temp_file = f.name
    
    manager = PortfolioManager()
    
    try:
        positions = manager.load_from_csv(temp_file)
        print(f"✓ Successfully loaded {len(positions)} positions")
        
        # Check that all tickers are uppercase
        for pos in positions:
            if pos.ticker != pos.ticker.upper():
                print(f"✗ Ticker not converted to uppercase: {pos.ticker}")
                return False
        
        print("✓ All tickers converted to uppercase:")
        for pos in positions:
            print(f"  {pos.ticker}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_portfolio_position_validation():
    """Test PortfolioPosition validation."""
    print("\n" + "=" * 60)
    print("Test 7: PortfolioPosition Validation")
    print("=" * 60)
    
    test_cases = [
        ("Valid position", lambda: PortfolioPosition("AAPL", 10, 150.25), True),
        ("Zero quantity", lambda: PortfolioPosition("AAPL", 0, 150.25), False),
        ("Negative quantity", lambda: PortfolioPosition("AAPL", -5, 150.25), False),
        ("Zero price", lambda: PortfolioPosition("AAPL", 10, 0), False),
        ("Negative price", lambda: PortfolioPosition("AAPL", 10, -150.25), False),
        ("Valid with decimal", lambda: PortfolioPosition("MSFT", 5.5, 300.50), True),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for name, create_func, should_succeed in test_cases:
        try:
            position = create_func()
            if should_succeed:
                print(f"✓ {name}: Created successfully - {position}")
                passed += 1
            else:
                print(f"✗ {name}: Should have failed but didn't")
        except ValueError as e:
            if not should_succeed:
                print(f"✓ {name}: Correctly failed with: {e}")
                passed += 1
            else:
                print(f"✗ {name}: Should have succeeded but failed with: {e}")
        except Exception as e:
            print(f"✗ {name}: Unexpected error: {e}")
    
    print(f"\n  Validation tests: {passed}/{total} passed")
    return passed == total


def test_save_and_reload():
    """Test saving to CSV and reloading."""
    print("\n" + "=" * 60)
    print("Test 8: Save and Reload")
    print("=" * 60)
    
    # Create a manager with some positions
    manager1 = PortfolioManager()
    positions = [
        PortfolioPosition("AAPL", 10, 150.25),
        PortfolioPosition("MSFT", 5, 300.50),
        PortfolioPosition("GOOGL", 2, 2800.75),
    ]
    
    for pos in positions:
        manager1.add_position(pos)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_file = f.name
    
    try:
        manager1.save_to_csv(temp_file)
        print(f"✓ Saved {manager1.total_positions} positions to {temp_file}")
        
        # Create new manager and load from saved file
        manager2 = PortfolioManager()
        loaded_positions = manager2.load_from_csv(temp_file)
        
        print(f"✓ Loaded {len(loaded_positions)} positions from saved file")
        
        # Verify positions match
        if len(manager1.positions) != len(manager2.positions):
            print("✗ Position counts don't match")
            return False
        
        for i, (pos1, pos2) in enumerate(zip(manager1.positions, manager2.positions)):
            if pos1.ticker != pos2.ticker or pos1.quantity != pos2.quantity or pos1.average_price != pos2.average_price:
                print(f"✗ Position {i} doesn't match")
                print(f"  Original: {pos1}")
                print(f"  Loaded: {pos2}")
                return False
        
        print("✓ All positions match exactly")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def main():
    """Run all tests."""
    print("Portfolio Manager CSV Loading Tests")
    print("=" * 60)
    
    tests = [
        test_successful_csv_loading,
        test_file_not_found,
        test_invalid_csv_format,
        test_invalid_numeric_data,
        test_empty_ticker,
        test_case_insensitive_ticker,
        test_portfolio_position_validation,
        test_save_and_reload,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Summary: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("✓ All tests passed successfully!")
        return 0
    else:
        print(f"✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())