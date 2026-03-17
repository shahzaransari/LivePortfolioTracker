"""
Module 6: Streamlit Dashboard for Live Portfolio Tracker

This module provides a modern web interface for the portfolio tracker using Streamlit.
It integrates all components (PortfolioManager, MarketDataFetcher, ValuationEngine) into a
beautiful, interactive web dashboard with real-time updates and visualizations.

Requirements:
    pip install streamlit plotly pandas yfinance

Features:
    - Modern, responsive web interface
    - Interactive charts using Plotly
    - Real-time portfolio valuation
    - Sidebar controls for adding/removing positions
    - Automatic data refresh
    - Color-coded P&L metrics
    - Multi-currency support

Usage:
    streamlit run app.py

Note:
    - The dashboard automatically loads portfolio.csv
    - Edit portfolio.csv or use the sidebar to modify holdings
    - Charts update automatically when data changes
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time
from datetime import datetime
import logging
import sys
import os

# Import our custom modules
try:
    from config import config
    from portfolio_manager import PortfolioManager, PortfolioPosition
    from market_data import MarketDataFetcher, PriceData
    from valuation import ValuationEngine
except ImportError as e:
    st.error(f"Error importing portfolio tracker modules: {e}")
    st.error("Make sure all required modules (config.py, portfolio_manager.py, etc.) are in the same directory.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.debug_mode else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Aurora Live Portfolio Tracker",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Animated Aurora Background
st.markdown("""
<style>
    /* Aurora background canvas */
    .ambient-canvas {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        pointer-events: none;
        overflow: hidden;
    }
    
    /* Aurora orbs */
    .orb {
        position: absolute;
        border-radius: 50%;
        filter: blur(80px);
        opacity: 0.6;
        animation: floatOrb 20s infinite ease-in-out;
    }
    
    /* Orb 1 - Indigo */
    .orb:nth-child(1) {
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, #4f46e5, transparent 70%);
        top: 10%;
        left: 10%;
        animation-delay: 0s;
    }
    
    /* Orb 2 - Fuchsia */
    .orb:nth-child(2) {
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, #c026d3, transparent 70%);
        top: 60%;
        right: 15%;
        animation-delay: 5s;
    }
    
    /* Orb 3 - Cyan */
    .orb:nth-child(3) {
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, #06b6d4, transparent 70%);
        bottom: 20%;
        left: 30%;
        animation-delay: 10s;
    }
    
    /* Orb floating animation */
    @keyframes floatOrb {
        0%, 100% {
            transform: translate(0, 0) scale(1);
        }
        25% {
            transform: translate(30px, -20px) scale(1.1);
        }
        50% {
            transform: translate(-20px, 30px) scale(0.9);
        }
        75% {
            transform: translate(-30px, -30px) scale(1.05);
        }
    }
    
    /* Import Aurora fonts */
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Main container - transparent to show Aurora background */
    .stApp {
        background: transparent !important;
    }
    
    /* Headers with Syne font */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 800 !important;
    }
    
    h1 {
        font-size: 3rem !important;
        background: linear-gradient(to bottom, #fff, #aaa) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        margin-bottom: 1.5rem !important;
        letter-spacing: -0.02em !important;
    }
    
    h2 {
        font-size: 2rem !important;
        color: #ffffff !important;
        margin-bottom: 1.5rem !important;
        position: relative;
        padding-bottom: 0.5rem;
    }
    
    h2::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #4f46e5, #c026d3, #06b6d4);
        border-radius: 2px;
    }
    
    h3 {
        font-size: 1.5rem !important;
        color: #06b6d4 !important;
    }
    
    /* Body text with Inter font */
    body, .stMarkdown, .stText, .stDataFrame, .stMetric, .stButton, .stSelectbox, .stTextInput {
        font-family: 'Inter', sans-serif !important;
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Glassmorphism Card styling for metric containers */
    div[data-testid="stMetric"], .stMetric {
        background: rgba(15, 15, 20, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(40px) !important;
        border-radius: 24px !important;
        padding: 1.5rem !important;
        transition: transform 0.3s ease !important;
    }
    
    div[data-testid="stMetric"]:hover, .stMetric:hover {
        transform: translateY(-5px) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Metric value styling */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        font-family: 'Syne', sans-serif !important;
    }
    
    /* Metric label styling */
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        color: rgba(255, 255, 255, 0.7) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        font-weight: 600 !important;
    }
    
    /* Metric delta styling */
    div[data-testid="stMetricDelta"] {
        font-weight: 600 !important;
        font-family: 'Syne', sans-serif !important;
    }
    
    div[data-testid="stMetricDelta"]:contains("+") {
        color: #06b6d4 !important;
    }
    
    div[data-testid="stMetricDelta"]:contains("-") {
        color: #c026d3 !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: rgba(10, 10, 15, 0.8) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(40px) !important;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(90deg, #4f46e5, #c026d3) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 20px rgba(79, 70, 229, 0.3) !important;
    }
    
    /* Secondary button styling */
    .stButton button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.1) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    .stButton button[kind="secondary"]:hover {
        border-color: #06b6d4 !important;
        background: rgba(6, 182, 212, 0.1) !important;
        box-shadow: 0 10px 20px rgba(6, 182, 212, 0.2) !important;
    }
    
    /* Dataframe styling - Glassmorphism */
    .stDataFrame {
        background: rgba(15, 15, 20, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 24px !important;
        overflow: hidden !important;
        backdrop-filter: blur(40px) !important;
        transition: transform 0.3s ease !important;
    }
    
    .stDataFrame:hover {
        transform: translateY(-5px) !important;
    }
    
    /* Table header styling */
    .stDataFrame thead th {
        background: linear-gradient(90deg, rgba(79, 70, 229, 0.2), rgba(192, 38, 211, 0.2)) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        font-family: 'Syne', sans-serif !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 1rem !important;
    }
    
    /* Table cell styling */
    .stDataFrame tbody td {
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
        color: rgba(255, 255, 255, 0.9) !important;
        padding: 0.75rem 1rem !important;
    }
    
    /* Table row hover effect */
    .stDataFrame tbody tr:hover {
        background: rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Divider styling */
    .stDivider {
        border-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(15, 15, 20, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        color: #06b6d4 !important;
        font-weight: 600 !important;
        font-family: 'Syne', sans-serif !important;
        backdrop-filter: blur(40px) !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: #06b6d4 !important;
        background: rgba(6, 182, 212, 0.1) !important;
    }
    
    /* Input field styling */
    .stTextInput input, .stNumberInput input, .stSelectbox select {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 0.75rem !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {
        border-color: #4f46e5 !important;
        box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.2) !important;
        background: rgba(79, 70, 229, 0.05) !important;
    }
    
    /* Success/Error/Info/Warning messages */
    .stAlert {
        background: rgba(15, 15, 20, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(40px) !important;
    }
    
    .stSuccess {
        border-left: 4px solid #06b6d4 !important;
    }
    
    .stError {
        border-left: 4px solid #c026d3 !important;
    }
    
    .stWarning {
        border-left: 4px solid #f59e0b !important;
    }
    
    .stInfo {
        border-left: 4px solid #4f46e5 !important;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-color: #4f46e5 transparent transparent transparent !important;
    }
    
    /* Caption styling */
    .stCaption {
        color: rgba(255, 255, 255, 0.6) !important;
        font-size: 0.85rem !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #4f46e5, #c026d3);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #4f46e5, #06b6d4);
    }
</style>

<div class="ambient-canvas">
    <div class="orb"></div>
    <div class="orb"></div>
    <div class="orb"></div>
</div>
""", unsafe_allow_html=True)

# Initialize session state for persistent objects
def initialize_session_state():
    """Initialize session state with portfolio manager, data fetcher, and valuation engine."""
    if 'portfolio_manager' not in st.session_state:
        st.session_state.portfolio_manager = PortfolioManager()
        logger.info("Initialized PortfolioManager in session state")
    
    if 'market_data_fetcher' not in st.session_state:
        st.session_state.market_data_fetcher = MarketDataFetcher()
        logger.info("Initialized MarketDataFetcher in session state")
    
    if 'valuation_engine' not in st.session_state:
        st.session_state.valuation_engine = ValuationEngine()
        logger.info("Initialized ValuationEngine in session state")
    
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = None
    
    if 'portfolio_loaded' not in st.session_state:
        st.session_state.portfolio_loaded = False
    
    if 'valuation_df' not in st.session_state:
        st.session_state.valuation_df = pd.DataFrame()

def load_portfolio():
    """Load portfolio from CSV file."""
    portfolio_file = "portfolio.csv"
    
    # Create dummy portfolio if it doesn't exist
    if not os.path.exists(portfolio_file):
        st.warning(f"Portfolio file '{portfolio_file}' not found. Creating dummy portfolio...")
        create_dummy_portfolio(portfolio_file)
    
    try:
        positions = st.session_state.portfolio_manager.load_from_csv(portfolio_file)
        st.session_state.portfolio_loaded = True
        logger.info(f"Loaded {len(positions)} positions from {portfolio_file}")
        return positions
    except Exception as e:
        st.error(f"Failed to load portfolio: {e}")
        logger.error(f"Error loading portfolio: {e}")
        return []

def create_dummy_portfolio(filepath: str = "portfolio.csv") -> None:
    """Create a dummy portfolio CSV file if it doesn't exist."""
    if os.path.exists(filepath):
        return
    
    logger.info(f"Creating dummy portfolio file: {filepath}")
    
    # Create a diverse dummy portfolio with global stocks
    dummy_portfolio = """Ticker,Quantity,AveragePrice
AAPL,10,150.25
MSFT,5,300.50
GOOGL,2,2800.00
TSLA,15,200.40
AMZN,3,3500.25
NVDA,8,450.50
"""
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(dummy_portfolio)
        logger.info(f"Created dummy portfolio with 6 stocks")
    except Exception as e:
        logger.error(f"Failed to create dummy portfolio: {e}")
        raise

def refresh_market_data(positions):
    """Refresh market data for all positions."""
    if not positions:
        return {}
    
    tickers = [pos.ticker for pos in positions]
    
    with st.spinner(f"Fetching live prices for {len(tickers)} tickers..."):
        try:
            live_prices = st.session_state.market_data_fetcher.get_live_prices(tickers)
            st.session_state.last_refresh = datetime.now()
            logger.info(f"Fetched prices for {len(live_prices)}/{len(tickers)} tickers")
            
            if len(live_prices) < len(tickers):
                missing = set(tickers) - set(live_prices.keys())
                logger.warning(f"Could not fetch prices for {len(missing)} tickers: {list(missing)}")
            
            return live_prices
        except Exception as e:
            st.error(f"Error fetching market data: {e}")
            logger.error(f"Error fetching market data: {e}")
            return {}

def evaluate_portfolio(positions, live_prices):
    """Evaluate portfolio and return valuation DataFrame."""
    if not positions:
        return pd.DataFrame()
    
    with st.spinner("Evaluating portfolio..."):
        try:
            valuation_df = st.session_state.valuation_engine.evaluate_portfolio(positions, live_prices)
            st.session_state.valuation_df = valuation_df
            logger.info(f"Portfolio evaluation completed: {len(valuation_df)-1 if not valuation_df.empty else 0} positions evaluated")
            return valuation_df
        except Exception as e:
            st.error(f"Error evaluating portfolio: {e}")
            logger.error(f"Error evaluating portfolio: {e}")
            return pd.DataFrame()

def get_portfolio_summary(valuation_df):
    """Calculate portfolio summary metrics from valuation DataFrame."""
    if valuation_df.empty:
        return {}
    
    # Get total row
    total_row = valuation_df[valuation_df['Ticker'] == 'TOTAL']
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
    
    for _, row in valuation_df.iterrows():
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
        'total_positions': len(valuation_df) - 1,  # Exclude TOTAL row
        'winning_positions': winning_positions,
        'losing_positions': losing_positions,
        'neutral_positions': neutral_positions,
        'total_investment': total_cost,
        'current_value': total_value,
        'total_pnl_dollar': total_pnl_dollar,
        'total_pnl_percent': total_pnl_percent
    }

def create_allocation_chart(valuation_df):
    """Create a donut chart showing portfolio allocation by ticker."""
    if valuation_df.empty or len(valuation_df) <= 1:  # Only TOTAL row
        return None
    
    # Filter out TOTAL row and rows with NaN current value
    df_filtered = valuation_df[valuation_df['Ticker'] != 'TOTAL'].copy()
    df_filtered = df_filtered.dropna(subset=['Current Value (Base Currency)'])
    
    if df_filtered.empty:
        return None
    
    # Aurora colors
    aurora_colors = ['#4f46e5', '#c026d3', '#06b6d4', '#8b5cf6', '#ec4899', '#0ea5e9']
    
    # Create donut chart
    fig = px.pie(
        df_filtered,
        values='Current Value (Base Currency)',
        names='Ticker',
        title='PORTFOLIO AURORA',
        hole=0.4,
        color_discrete_sequence=aurora_colors
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Value: $%{value:,.2f}<br>%{percent}',
        marker=dict(line=dict(color='rgba(255,255,255,0.1)', width=2))
    )
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
        title_font_size=20,
        title_font_family='Syne',
        title_font_color='#ffffff',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(family='Inter', size=12, color='rgba(255,255,255,0.8)'),
            bgcolor='rgba(15,15,20,0.7)',
            bordercolor='rgba(255,255,255,0.1)',
            borderwidth=1,
            itemwidth=30
        ),
        height=450,
        font=dict(family='Inter', size=12, color='rgba(255,255,255,0.8)'),
        hoverlabel=dict(
            bgcolor='rgba(15,15,20,0.9)',
            font_size=12,
            font_family='Inter',
            bordercolor='rgba(255,255,255,0.1)'
        )
    )
    
    return fig

def create_pnl_chart(valuation_df):
    """Create a bar chart showing P&L by ticker."""
    if valuation_df.empty or len(valuation_df) <= 1:  # Only TOTAL row
        return None
    
    # Filter out TOTAL row and rows with NaN P&L
    df_filtered = valuation_df[valuation_df['Ticker'] != 'TOTAL'].copy()
    df_filtered = df_filtered.dropna(subset=['P&L ($ Base)'])
    
    if df_filtered.empty:
        return None
    
    # Sort by P&L for better visualization
    df_filtered = df_filtered.sort_values('P&L ($ Base)', ascending=False)
    
    # Create color array based on P&L values using Aurora colors
    colors = ['#06b6d4' if x >= 0 else '#c026d3' for x in df_filtered['P&L ($ Base)']]
    
    # Create bar chart
    fig = px.bar(
        df_filtered,
        x='Ticker',
        y='P&L ($ Base)',
        title='AURORA P&L',
        color=colors,
        color_discrete_map={'#06b6d4': '#06b6d4', '#c026d3': '#c026d3'},
        text=df_filtered['P&L ($ Base)'].apply(lambda x: f'${x:+,.2f}')
    )
    
    fig.update_traces(
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>P&L: $%{y:+,.2f}<extra></extra>',
        marker=dict(line=dict(color='rgba(255,255,255,0.1)', width=1))
    )
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        title_x=0.5,
        title_font_size=20,
        title_font_family='Syne',
        title_font_color='#ffffff',
        xaxis_title="TICKER",
        yaxis_title="P&L ($)",
        showlegend=False,
        height=450,
        font=dict(family='Inter', size=12, color='rgba(255,255,255,0.8)'),
        xaxis=dict(
            tickfont=dict(family='Inter', size=11, color='rgba(255,255,255,0.7)'),
            title_font=dict(family='Syne', size=14, color='#4f46e5'),
            tickangle=45
        ),
        yaxis=dict(
            tickformat="$,.0f",
            tickfont=dict(family='Inter', size=11, color='rgba(255,255,255,0.7)'),
            title_font=dict(family='Syne', size=14, color='#4f46e5'),
            gridcolor='rgba(255,255,255,0.1)',
            zerolinecolor='rgba(255,255,255,0.3)'
        ),
        hoverlabel=dict(
            bgcolor='rgba(15,15,20,0.9)',
            font_size=12,
            font_family='Inter',
            bordercolor='rgba(255,255,255,0.1)'
        )
    )
    
    # Add horizontal line at y=0 with Aurora styling
    fig.add_hline(
        y=0, 
        line_width=2, 
        line_dash="solid", 
        line_color="rgba(255,255,255,0.3)",
        annotation_text="BREAKEVEN",
        annotation_position="bottom right",
        annotation_font=dict(family='Syne', size=10, color='rgba(255,255,255,0.6)'),
        annotation_bgcolor='rgba(15,15,20,0.7)',
        annotation_bordercolor='rgba(255,255,255,0.1)'
    )
    
    return fig

def format_valuation_dataframe(df):
    """Format the valuation DataFrame for display."""
    if df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    df_display = df.copy()
    
    # Format numeric columns
    numeric_columns = [
        'Shares',
        'Avg Cost (Native)',
        'Current Price (Native)',
        'Total Cost (Base Currency)',
        'Current Value (Base Currency)',
        'P&L ($ Base)',
        'P&L (%)'
    ]
    
    for col in numeric_columns:
        if col in df_display.columns:
            if col in ['P&L (%)']:
                df_display[col] = df_display[col].apply(
                    lambda x: f"{x:+.2f}%" if not pd.isna(x) else "N/A"
                )
            elif col in ['Total Cost (Base Currency)', 'Current Value (Base Currency)', 'P&L ($ Base)']:
                df_display[col] = df_display[col].apply(
                    lambda x: f"${x:,.2f}" if not pd.isna(x) else "N/A"
                )
            elif col in ['Avg Cost (Native)', 'Current Price (Native)']:
                df_display[col] = df_display[col].apply(
                    lambda x: f"{x:,.2f}" if not pd.isna(x) else "N/A"
                )
            elif col == 'Shares':
                df_display[col] = df_display[col].apply(
                    lambda x: f"{x:,.2f}" if not pd.isna(x) else "N/A"
                )
    
    return df_display

def main():
    """Main function to run the Streamlit dashboard."""
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<h1>AURORA LIVE PORTFOLIO TRACKER</h1>', unsafe_allow_html=True)
    st.markdown("Interactive financial analytics with real-time valuation and aurora-inspired visualization")
    
    # Load portfolio
    positions = load_portfolio()
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Dashboard Controls")
        
        # Refresh button
        if st.button("🔄 Refresh Market Data", type="primary", use_container_width=True):
            if positions:
                live_prices = refresh_market_data(positions)
                if live_prices:
                    valuation_df = evaluate_portfolio(positions, live_prices)
                    st.success("Market data refreshed successfully!")
            else:
                st.warning("No positions to refresh")
        
        # Last refresh time
        if st.session_state.last_refresh:
            st.caption(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
        
        st.divider()
        
        # Add position form
        with st.expander("➕ Add New Position", expanded=False):
            with st.form("add_position_form"):
                ticker = st.text_input("Ticker Symbol", placeholder="AAPL").upper()
                quantity = st.number_input("Quantity", min_value=0.01, value=1.0, step=0.01)
                avg_price = st.number_input("Average Price", min_value=0.01, value=100.0, step=0.01)
                
                if st.form_submit_button("Add Position", type="secondary"):
                    if ticker and quantity > 0 and avg_price > 0:
                        try:
                            new_position = PortfolioPosition(
                                ticker=ticker,
                                quantity=quantity,
                                average_price=avg_price
                            )
                            st.session_state.portfolio_manager.add_position(new_position)
                            st.session_state.portfolio_manager.save_to_csv("portfolio.csv")
                            st.success(f"Added position: {ticker}")
                            st.rerun()
                        except ValueError as e:
                            st.error(f"Error adding position: {e}")
                    else:
                        st.error("Please fill all fields with valid values")
        
        # Remove position form
        with st.expander("🗑️ Remove Position", expanded=False):
            if positions:
                ticker_options = [pos.ticker for pos in positions]
                ticker_to_remove = st.selectbox("Select Ticker to Remove", ticker_options)
                
                if st.button("Remove Position", type="secondary", use_container_width=True):
                    removed = st.session_state.portfolio_manager.remove_position(ticker_to_remove)
                    if removed:
                        st.session_state.portfolio_manager.save_to_csv("portfolio.csv")
                        st.success(f"Removed position: {ticker_to_remove}")
                        st.rerun()
            else:
                st.info("No positions to remove")
        
        st.divider()
        
        # Portfolio info
        st.markdown("### 📋 Portfolio Info")
        if positions:
            st.metric("Total Positions", len(positions))
            total_investment = sum(pos.total_cost for pos in positions)
            st.metric("Total Investment", f"${total_investment:,.2f}")
        else:
            st.info("Portfolio is empty")
        
        # Cache info
        if st.session_state.market_data_fetcher:
            cache_info = st.session_state.market_data_fetcher.get_cache_info()
            st.caption(f"Price cache: {cache_info['valid_entries']} valid entries")
        
        st.divider()
        
        # Instructions
        with st.expander("ℹ️ How to use"):
            st.markdown("""
            1. **Add positions** using the form in the sidebar
            2. **Refresh market data** to get latest prices
            3. **View charts** for allocation and P&L analysis
            4. **Edit portfolio.csv** directly or use the sidebar controls
            5. **Remove positions** using the remove form
            
            The dashboard automatically saves changes to portfolio.csv.
            """)
    
    # Main content area
    if not positions:
        st.info("💡 Your portfolio is empty. Add positions using the sidebar to get started!")
        return
    
    # Refresh data on initial load or when needed
    if st.session_state.valuation_df.empty or st.session_state.last_refresh is None:
        live_prices = refresh_market_data(positions)
        if live_prices:
            valuation_df = evaluate_portfolio(positions, live_prices)
        else:
            valuation_df = pd.DataFrame()
    else:
        valuation_df = st.session_state.valuation_df
    
    if valuation_df.empty:
        st.warning("Unable to load valuation data. Please check your internet connection and try refreshing.")
        return
    
    # Portfolio Summary Metrics (Top Row)
    st.markdown('<h2>OVERVIEW</h2>', unsafe_allow_html=True)
    
    summary = get_portfolio_summary(valuation_df)
    if summary:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Investment",
                value=f"${summary['total_investment']:,.2f}" if not pd.isna(summary['total_investment']) else "N/A"
            )
        
        with col2:
            st.metric(
                label="Current Value",
                value=f"${summary['current_value']:,.2f}" if not pd.isna(summary['current_value']) else "N/A"
            )
        
        with col3:
            delta_color = "normal"
            delta_value = None
            if not pd.isna(summary['total_pnl_dollar']):
                delta_value = f"${summary['total_pnl_dollar']:+,.2f}"
                delta_color = "normal"
            
            st.metric(
                label="Total P&L ($)",
                value=f"${summary['total_pnl_dollar']:+,.2f}" if not pd.isna(summary['total_pnl_dollar']) else "N/A",
                delta=delta_value,
                delta_color=delta_color
            )
        
        with col4:
            delta_color = "normal"
            delta_value = None
            if not pd.isna(summary['total_pnl_percent']):
                delta_value = f"{summary['total_pnl_percent']:+.2f}%"
                delta_color = "normal"
            
            st.metric(
                label="Total P&L (%)",
                value=f"{summary['total_pnl_percent']:+.2f}%" if not pd.isna(summary['total_pnl_percent']) else "N/A",
                delta=delta_value,
                delta_color=delta_color
            )
    
    st.divider()
    
    # Charts (Middle Row)
    st.markdown('<h2>ANALYTICS</h2>', unsafe_allow_html=True)
    
    if len(valuation_df) > 1:  # More than just TOTAL row
        col1, col2 = st.columns(2)
        
        with col1:
            allocation_chart = create_allocation_chart(valuation_df)
            if allocation_chart:
                st.plotly_chart(allocation_chart, use_container_width=True)
            else:
                st.info("No allocation data available for chart")
        
        with col2:
            pnl_chart = create_pnl_chart(valuation_df)
            if pnl_chart:
                st.plotly_chart(pnl_chart, use_container_width=True)
            else:
                st.info("No P&L data available for chart")
    else:
        st.info("Add more positions to see portfolio charts and analytics")
    
    st.divider()
    
    # Data Table (Bottom Row)
    st.markdown('<h2>VALUATION</h2>', unsafe_allow_html=True)
    
    # Format the DataFrame for display
    df_display = format_valuation_dataframe(valuation_df)
    
    # Display the DataFrame
    if not df_display.empty:
        # Apply conditional formatting for P&L columns with Aurora colors
        def color_pnl(val):
            if isinstance(val, str) and val != "N/A":
                if val.startswith("-$") or val.endswith("-%"):
                    return 'color: #c026d3; font-weight: 600'
                elif val.startswith("+$") or val.endswith("+%"):
                    return 'color: #06b6d4; font-weight: 600'
            return ''
        
        # Create styled DataFrame
        styled_df = df_display.style.applymap(color_pnl, subset=['P&L ($ Base)', 'P&L (%)'])
        
        # Display with Streamlit
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Ticker': st.column_config.TextColumn("Ticker", width="small"),
                'Shares': st.column_config.NumberColumn("Shares", format="%.2f"),
                'Native Currency': st.column_config.TextColumn("Currency", width="small"),
                'Avg Cost (Native)': st.column_config.NumberColumn("Avg Cost", format="%.2f"),
                'Current Price (Native)': st.column_config.NumberColumn("Curr Price", format="%.2f"),
                'Total Cost (Base Currency)': st.column_config.NumberColumn("Total Cost", format="$%.2f"),
                'Current Value (Base Currency)': st.column_config.NumberColumn("Current Value", format="$%.2f"),
                'P&L ($ Base)': st.column_config.TextColumn("P&L ($)"),
                'P&L (%)': st.column_config.TextColumn("P&L (%)")
            }
        )
        
        # Download button for valuation data
        csv = valuation_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Valuation Data (CSV)",
            data=csv,
            file_name=f"portfolio_valuation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("No valuation data to display")
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"Base Currency: {config.default_currency}")
    with col2:
        if st.session_state.last_refresh:
            st.caption(f"Last updated: {st.session_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    with col3:
        st.caption(f"Total positions: {len(positions)}")

if __name__ == "__main__":
    main()