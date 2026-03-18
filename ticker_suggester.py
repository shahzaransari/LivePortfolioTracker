"""
Module 7: Ticker Suggester

This module provides a lightweight ticker suggestion system that fetches S&P 500 companies
from Wikipedia and appends curated European and Indian tickers. It's designed to be robust
and doesn't require external API keys.

Features:
    - Fetches S&P 500 list from Wikipedia using pandas.read_html
    - Adds curated European (.DE, .L) and Indian (.NS, .BO) tickers
    - Caches results using Streamlit's caching mechanism
    - Returns formatted strings for display in dropdowns

Usage:
    suggester = TickerSuggester()
    ticker_list = suggester.get_ticker_list()
    # Returns: ["Apple Inc. (AAPL)", "NVIDIA Corp (NVDA)", ...]
"""

import streamlit as st
import pandas as pd
import logging
from typing import List, Optional
import time

logger = logging.getLogger(__name__)


class TickerSuggester:
    """
    A class to provide ticker suggestions from S&P 500 and curated international stocks.
    
    The class fetches S&P 500 companies from Wikipedia and adds manually curated
    European and Indian tickers. Results are cached to avoid repeated network calls.
    """
    
    def __init__(self):
        """Initialize the TickerSuggester."""
        self._cached_ticker_list: Optional[List[str]] = None
        self._last_fetch_time: Optional[float] = None
        logger.info("TickerSuggester initialized")
    
    @st.cache_data(ttl=86400)  # Cache for 24 hours
    def _fetch_sp500_tickers(_self) -> List[str]:
        """
        Fetch S&P 500 tickers from Wikipedia.
        
        Returns:
            List of formatted strings: ["Company Name (TICKER)", ...]
            
        Raises:
            Exception: If Wikipedia fetch fails
        """
        try:
            logger.info("Fetching S&P 500 tickers from Wikipedia...")
            
            # Wikipedia page for S&P 500 components
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            
            # Read tables from Wikipedia
            tables = pd.read_html(url)
            
            # The first table contains the S&P 500 components
            sp500_table = tables[0]
            
            # Extract company names and tickers
            # Column names might vary, so we look for common patterns
            if 'Security' in sp500_table.columns and 'Symbol' in sp500_table.columns:
                company_names = sp500_table['Security']
                tickers = sp500_table['Symbol']
            elif 'Company' in sp500_table.columns and 'Symbol' in sp500_table.columns:
                company_names = sp500_table['Company']
                tickers = sp500_table['Symbol']
            else:
                # Fallback: use first two columns
                company_names = sp500_table.iloc[:, 0]
                tickers = sp500_table.iloc[:, 1]
            
            # Format as "Company Name (TICKER)"
            formatted_tickers = [
                f"{company} ({ticker})"
                for company, ticker in zip(company_names, tickers)
                if pd.notna(company) and pd.notna(ticker)
            ]
            
            logger.info(f"Successfully fetched {len(formatted_tickers)} S&P 500 tickers")
            return formatted_tickers
            
        except Exception as e:
            logger.error(f"Failed to fetch S&P 500 tickers from Wikipedia: {e}")
            
            # Fallback: return a curated list of major US stocks
            logger.info("Using fallback US ticker list")
            fallback_us = [
                "Apple Inc. (AAPL)",
                "Microsoft Corp (MSFT)",
                "Amazon.com Inc (AMZN)",
                "Alphabet Inc (GOOGL)",
                "Meta Platforms Inc (META)",
                "Tesla Inc (TSLA)",
                "NVIDIA Corp (NVDA)",
                "Berkshire Hathaway (BRK.B)",
                "JPMorgan Chase & Co (JPM)",
                "Johnson & Johnson (JNJ)",
                "Visa Inc (V)",
                "Procter & Gamble Co (PG)",
                "UnitedHealth Group Inc (UNH)",
                "Home Depot Inc (HD)",
                "Mastercard Inc (MA)",
                "Bank of America Corp (BAC)",
                "Pfizer Inc (PFE)",
                "Netflix Inc (NFLX)",
                "Adobe Inc (ADBE)",
                "Salesforce Inc (CRM)"
            ]
            return fallback_us
    
    def _get_curated_international_tickers(self) -> List[str]:
        """
        Return a curated list of international tickers (European and Indian).
        
        Returns:
            List of formatted strings for international companies
        """
        # Curated European tickers
        european_tickers = [
            # German (.DE)
            "SAP SE (SAP.DE)",
            "Volkswagen AG (VOW3.DE)",
            "Siemens AG (SIE.DE)",
            "Allianz SE (ALV.DE)",
            "Deutsche Bank AG (DBK.DE)",
            "BASF SE (BAS.DE)",
            "Bayer AG (BAYN.DE)",
            "BMW AG (BMW.DE)",
            "Daimler Truck Holding AG (DTG.DE)",
            "Adidas AG (ADS.DE)",
            
            # London (.L)
            "HSBC Holdings plc (HSBA.L)",
            "BP plc (BP.L)",
            "GlaxoSmithKline plc (GSK.L)",
            "AstraZeneca plc (AZN.L)",
            "Unilever plc (ULVR.L)",
            "Rio Tinto plc (RIO.L)",
            "British American Tobacco plc (BATS.L)",
            "Diageo plc (DGE.L)",
            "Barclays plc (BARC.L)",
            "Lloyds Banking Group plc (LLOY.L)",
            
            # Other European
            "Nestlé SA (NESN.SW)",
            "Novartis AG (NOVN.SW)",
            "Roche Holding AG (ROG.SW)",
            "UBS Group AG (UBSG.SW)",
            "LVMH Moët Hennessy Louis Vuitton SE (MC.PA)",
            "Sanofi SA (SAN.PA)",
            "TotalEnergies SE (TTE.PA)",
            "L'Oréal SA (OR.PA)",
            "ASML Holding NV (ASML.AS)",
            "ING Groep NV (INGA.AS)"
        ]
        
        # Curated Indian tickers
        indian_tickers = [
            # National Stock Exchange (.NS)
            "Reliance Industries Ltd (RELIANCE.NS)",
            "Tata Consultancy Services Ltd (TCS.NS)",
            "HDFC Bank Ltd (HDFCBANK.NS)",
            "Infosys Ltd (INFY.NS)",
            "ICICI Bank Ltd (ICICIBANK.NS)",
            "Hindustan Unilever Ltd (HINDUNILVR.NS)",
            "State Bank of India (SBIN.NS)",
            "Bharti Airtel Ltd (BHARTIARTL.NS)",
            "Larsen & Toubro Ltd (LT.NS)",
            "Kotak Mahindra Bank Ltd (KOTAKBANK.NS)",
            "Axis Bank Ltd (AXISBANK.NS)",
            "Maruti Suzuki India Ltd (MARUTI.NS)",
            "Sun Pharmaceutical Industries Ltd (SUNPHARMA.NS)",
            "Titan Company Ltd (TITAN.NS)",
            "Wipro Ltd (WIPRO.NS)",
            
            # Bombay Stock Exchange (.BO)
            "Reliance Industries Ltd (RELIANCE.BO)",
            "Tata Consultancy Services Ltd (TCS.BO)",
            "HDFC Bank Ltd (HDFCBANK.BO)",
            "Infosys Ltd (INFY.BO)",
            "ICICI Bank Ltd (ICICIBANK.BO)"
        ]
        
        return european_tickers + indian_tickers
    
    def get_ticker_list(self, include_international: bool = True) -> List[str]:
        """
        Get the complete list of suggested tickers.
        
        Args:
            include_international: Whether to include European and Indian tickers
            
        Returns:
            List of formatted strings: ["Company Name (TICKER)", ...]
        """
        # Use cached list if available and recent
        if self._cached_ticker_list is not None and self._last_fetch_time is not None:
            # If cache is less than 1 hour old, use it
            if time.time() - self._last_fetch_time < 3600:
                logger.debug("Using cached ticker list")
                return self._cached_ticker_list
        
        try:
            # Fetch S&P 500 tickers
            sp500_tickers = self._fetch_sp500_tickers()
            
            # Add international tickers if requested
            if include_international:
                international_tickers = self._get_curated_international_tickers()
                all_tickers = sp500_tickers + international_tickers
            else:
                all_tickers = sp500_tickers
            
            # Remove duplicates while preserving order
            seen = set()
            unique_tickers = []
            for ticker in all_tickers:
                if ticker not in seen:
                    seen.add(ticker)
                    unique_tickers.append(ticker)
            
            # Sort alphabetically by company name
            unique_tickers.sort(key=lambda x: x.lower())
            
            # Cache the result
            self._cached_ticker_list = unique_tickers
            self._last_fetch_time = time.time()
            
            logger.info(f"Generated ticker list with {len(unique_tickers)} unique entries")
            return unique_tickers
            
        except Exception as e:
            logger.error(f"Error generating ticker list: {e}")
            
            # Return a minimal fallback list
            fallback = [
                "Apple Inc. (AAPL)",
                "Microsoft Corp (MSFT)",
                "Amazon.com Inc (AMZN)",
                "Alphabet Inc (GOOGL)",
                "Meta Platforms Inc (META)",
                "Tesla Inc (TSLA)",
                "NVIDIA Corp (NVDA)",
                "SAP SE (SAP.DE)",
                "Reliance Industries Ltd (RELIANCE.NS)"
            ]
            return fallback
    
    def extract_ticker_symbol(self, formatted_ticker: str) -> str:
        """
        Extract the ticker symbol from a formatted string.
        
        Args:
            formatted_ticker: String in format "Company Name (TICKER)"
            
        Returns:
            Ticker symbol (e.g., "AAPL", "SAP.DE", "RELIANCE.NS")
            
        Example:
            >>> extract_ticker_symbol("Apple Inc. (AAPL)")
            "AAPL"
            >>> extract_ticker_symbol("Reliance Industries Ltd (RELIANCE.NS)")
            "RELIANCE.NS"
        """
        try:
            # Find the last occurrence of '(' and ')'
            start = formatted_ticker.rfind('(')
            end = formatted_ticker.rfind(')')
            
            if start != -1 and end != -1 and start < end:
                ticker = formatted_ticker[start + 1:end].strip()
                return ticker
            else:
                # If no parentheses found, return the string as-is (might be raw ticker)
                return formatted_ticker.strip()
                
        except Exception as e:
            logger.error(f"Error extracting ticker symbol from '{formatted_ticker}': {e}")
            # Fallback: try to extract any uppercase letters/dots
            import re
            match = re.search(r'([A-Z]+(?:\.[A-Z]+)?)', formatted_ticker)
            if match:
                return match.group(1)
            return formatted_ticker.strip()


# Example usage
if __name__ == "__main__":
    # Test the TickerSuggester
    import sys
    
    print("Testing TickerSuggester...")
    suggester = TickerSuggester()
    
    # Get ticker list
    tickers = suggester.get_ticker_list()
    print(f"\nTotal tickers: {len(tickers)}")
    print("\nFirst 10 tickers:")
    for i, ticker in enumerate(tickers[:10], 1):
        print(f"{i}. {ticker}")
    
    print("\nLast 10 tickers:")
    for i, ticker in enumerate(tickers[-10:], len(tickers) - 9):
        print(f"{i}. {ticker}")
    
    # Test extraction
    print("\nTicker extraction examples:")
    test_cases = [
        "Apple Inc. (AAPL)",
        "NVIDIA Corp (NVDA)",
        "SAP SE (SAP.DE)",
        "Reliance Industries Ltd (RELIANCE.NS)",
        "HSBC Holdings plc (HSBA.L)"
    ]
    
    for test in test_cases:
        symbol = suggester.extract_ticker_symbol(test)
        print(f"  '{test}' -> '{symbol}'")
    
    print("\nTest completed successfully!")