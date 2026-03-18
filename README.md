# Live Portfolio Tracker - Streamlit Dashboard

## Overview
This is Streamlit Dashboard for the Live Portfolio Tracker project. It provides a modern web interface for portfolio tracking with real-time market data, interactive charts, and portfolio management capabilities.

## Features

### Dashboard Layout
- **Wide Layout**: Modern, responsive design with `layout="wide"`
- **Sidebar Controls**: Portfolio management tools and refresh controls
- **Top Row KPIs**: Key portfolio metrics with color-coded P&L
- **Middle Row Charts**: Interactive Plotly charts for allocation and P&L analysis
- **Bottom Row Data Table**: Detailed valuation data with formatting

### Functionality
- **Real-time Market Data**: Fetches live prices using yfinance
- **Portfolio Management**: Add/remove positions via sidebar forms
- **Multi-currency Support**: Handles stocks in different currencies
- **Interactive Charts**: 
  - Donut chart for portfolio allocation
  - Bar chart for P&L by ticker (green/red color coding)
- **Data Persistence**: Automatically saves to/loads from portfolio.csv
- **State Management**: Uses Streamlit session state for persistent objects

## Installation

1. Ensure you have Python 3.7+ installed
2. Install required packages:
   ```bash
   pip install streamlit plotly pandas yfinance
   ```
3. The dashboard automatically uses existing modules:
   - `config.py` - Configuration management
   - `portfolio_manager.py` - Portfolio data handling
   - `market_data.py` - Live market data fetching
   - `valuation.py` - Multi-currency portfolio valuation

## Usage

### Starting the Dashboard
```bash
streamlit run app.py
```

### Initial Setup
1. The dashboard will automatically create a `portfolio.csv` file with dummy data if none exists
2. You can edit this file directly or use the sidebar forms

### Dashboard Components

#### Sidebar Controls
- **Refresh Market Data**: Fetches latest prices for all positions
- **Add New Position**: Form to add stocks (Ticker, Quantity, Average Price)
- **Remove Position**: Select and remove existing positions
- **Portfolio Info**: Summary of current holdings

#### Main Dashboard
1. **Portfolio Overview** (Top Row):
   - Total Investment
   - Current Value
   - Total P&L ($) - Color-coded green/red
   - Total P&L (%) - Color-coded green/red

2. **Portfolio Analytics** (Middle Row):
   - Left: Portfolio Allocation Donut Chart
   - Right: P&L by Ticker Bar Chart

3. **Detailed Valuation** (Bottom Row):
   - Complete valuation DataFrame
   - Formatted currency values
   - Color-coded P&L columns
   - Download button for CSV export

### Portfolio Management
- **Adding Positions**: Use the sidebar form with Ticker, Quantity, and Average Price
- **Removing Positions**: Select from dropdown and confirm removal
- **Automatic Saving**: Changes are automatically saved to `portfolio.csv`
- **Data Refresh**: Click "Refresh Market Data" to update prices

## Configuration

The dashboard uses the existing `config.py` module for:
- Default currency (config.default_currency)
- Debug mode settings
- API key management (via .env file)

## Error Handling
- **Empty Portfolio**: Shows friendly message prompting user to add positions
- **Missing Data**: Gracefully handles missing prices or FX rates
- **Network Issues**: Provides clear error messages for data fetch failures
- **Invalid Input**: Validates form inputs before processing

## Integration with Existing Modules

The dashboard seamlessly integrates with the existing codebase:

1. **PortfolioManager**: Loads/saves portfolio data, manages positions
2. **MarketDataFetcher**: Fetches live prices with caching
3. **ValuationEngine**: Evaluates portfolio with multi-currency support
4. **Config**: Uses global configuration settings

## Customization

### Styling
- Custom CSS for improved visual appearance
- Color-coded metrics based on performance
- Responsive design for different screen sizes

### Charts
- Interactive Plotly charts with hover information
- Color schemes for better data visualization
- Automatic updates when data changes

## Troubleshooting

### Common Issues
1. **No data displayed**: Ensure `portfolio.csv` exists or add positions via sidebar
2. **Price fetch errors**: Check internet connection and yfinance availability
3. **Import errors**: Verify all required modules are in the same directory
4. **Currency conversion issues**: Check FX rate availability for non-USD stocks

### Logging
- Detailed logging available in console
- Debug mode can be enabled in config.py
- Error messages are displayed in the dashboard

## Performance
- **Caching**: Market prices cached for 30 seconds to reduce API calls
- **Session State**: Objects persist across reruns for efficiency
- **Batch Processing**: Fetches prices in batches for multiple tickers

## Security Notes
- API keys loaded from .env file (not hardcoded)
- No sensitive data exposed in frontend
- Input validation for all user submissions

## Next Steps
Potential enhancements:
- User authentication
- Historical performance charts
- Portfolio rebalancing suggestions
- Email/SMS alerts for price changes
- Multiple portfolio support