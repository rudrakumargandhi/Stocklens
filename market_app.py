import streamlit as st
from user_data import users, register_user, save_users, load_users
from stock_utility_handler import StockAPI, StockAnalyzer
from ai_insights_handler import AIInsights
import os

output_dir = "D:/Bollinger_analysis/images"
os.makedirs(output_dir, exist_ok=True)
# === Constants ===
ALPHA_VANTAGE_KEY = "5BPONE0YQY8ZH17G"
GOOGLE_API_KEY = "AIzaSyAIFQijh_mCe9tyU70jY8M_d--pAh8Ux9A"

# === Session State Initialization ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.page = "login"
    st.session_state.portfolio = []

# === Page: Login ===
def login_page():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in users and users[username]["password"] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = users[username]["role"]
            st.session_state.portfolio = users[username].get("portfolio", [])
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("Invalid credentials.")

    if st.button("Register New Account"):
        st.session_state.page = "register"
        st.rerun()

# === Page: Register ===
def register_page():
    st.title("Register")

    new_username = st.text_input("New Username")
    new_password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Create Account"):
        if not new_username or not new_password:
            st.warning("Fill all fields.")
        elif new_password != confirm_password:
            st.warning("Passwords do not match.")
        elif new_username in users:
            st.error("Username already exists.")
        else:
            register_user(new_username, new_password)
            st.success("Account created. Please login.")
            st.session_state.page = "login"
            st.rerun()

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

# === Page: Dashboard ===
def dashboard_page():
    st.title(f"Welcome, {st.session_state.username}!")

    col1, col2 = st.columns(2)
    with col1:
        # Don't assign to session_state["ticker"] here
        ticker_input = st.text_input("Stock Ticker (e.g., RELIANCE)", value=st.session_state.get("ticker", ""), key="ticker")
    with col2:
        market_input = st.selectbox("Market", ["BSE", "NASDAQ"], key="market")

    if st.button("Analyze"):
        st.session_state.page = "analysis"
        st.session_state.analysis_stock = ticker_input
        st.session_state.analysis_market = market_input
        st.rerun()

    st.subheader("📊 Portfolio")

    if st.session_state.portfolio:
        stock_api = StockAPI(ALPHA_VANTAGE_KEY)

        for stock in st.session_state.portfolio:
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.markdown(f"**{stock}**")
            with col2:
                try:
                    full_symbol = f"BOM:{stock}"  # assuming BSE stocks for now
                    price = stock_api.get_live_price(full_symbol, market="BSE")
                    st.markdown(f"₹ {price}")
                except Exception as e:
                    st.warning("N/A")
            with col3:
                if st.button(f"Analyze {stock}", key=f"analyze_{stock}"):
                    st.session_state.page = "analysis"
                    st.session_state.analysis_stock = stock
                    st.session_state.analysis_market = "BSE"  # default for now
                    st.rerun()
    else:
        st.info("No stocks in portfolio yet.")

    new_stock = st.text_input("Add to Portfolio")
    if st.button("Add Stock"):
        if new_stock and new_stock.upper() not in st.session_state.portfolio:
            st.session_state.portfolio.append(new_stock.upper())
            users[st.session_state.username]["portfolio"] = st.session_state.portfolio
            save_users(users)
            st.success(f"Added {new_stock.upper()} to portfolio.")
            st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.session_state.page = "login"
        st.rerun()
# === Page: Stock Analysis ===
def analysis_page():
    st.title("📈 Stock Analysis")

    ticker = st.session_state.get("analysis_stock")
    market = st.session_state.get("analysis_market")

    if not ticker or not market:
        st.warning("No stock selected. Please go to Dashboard and select a stock.")
        return

    st.markdown(f"**Analyzing:** `{ticker}` in `{market}`")

    stock_api = StockAPI(ALPHA_VANTAGE_KEY)
    analyzer = StockAnalyzer()
    ai_insights_obj = AIInsights()

    try:
        stock_data = stock_api.get_stock_data(ticker, market)
        df = analyzer.json_to_dataframe(stock_data, ticker, market)

        st.subheader("Price Chart with Indicators")

        image_path = os.path.join(output_dir, f"{ticker}_chart.png")
        fig = analyzer.plot_stock_data(df, ticker, market, image_path)
        st.pyplot(fig)

        st.subheader("📚 Fundamental Analysis")

        try:
            fundamental_data = stock_api.get_fundamental_data(ticker)

            selected_fields = {
                "Name": fundamental_data.get("Name", "N/A"),
                "Sector": fundamental_data.get("Sector", "N/A"),
                "MarketCapitalization": fundamental_data.get("MarketCapitalization", "N/A"),
                "PERatio": fundamental_data.get("PERatio", "N/A"),
                "EPS": fundamental_data.get("EPS", "N/A"),
                "DividendYield": fundamental_data.get("DividendYield", "N/A"),
                "ReturnOnEquityTTM": fundamental_data.get("ReturnOnEquityTTM", "N/A"),
                "RevenueTTM": fundamental_data.get("RevenueTTM", "N/A"),
                "ProfitMargin": fundamental_data.get("ProfitMargin", "N/A"),
                "52WeekHigh": fundamental_data.get("52WeekHigh", "N/A"),
                "52WeekLow": fundamental_data.get("52WeekLow", "N/A"),
            }

            for k, v in selected_fields.items():
                st.markdown(f"**{k.replace('_', ' ')}:** {v}")
        except Exception as e:
            st.warning(f"Could not load fundamentals: {e}")

        st.subheader("AI Insights")

        with st.spinner("Generating AI Insights..."):
            insights = ai_insights_obj.get_ai_insights(image_path, ticker, market, fundamentals=selected_fields)
            st.markdown(insights)

    except Exception as e:
        st.error(f"Error loading analysis: {e}")

    if st.button("Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

# === Main Control ===
def main():
    st.set_page_config(page_title="Stock AI Platform", layout="wide")

    page = st.session_state.get("page", "login")

    if page == "login":
        login_page()
    elif page == "register":
        register_page()
    elif page == "dashboard":
        dashboard_page()
    elif page == "analysis":
        analysis_page()

# === Run App ===
if __name__ == "__main__":
    main()
