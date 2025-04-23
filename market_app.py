import streamlit as st
from stock_utility_handler import StockAPI, StockAnalyzer
from ai_insights_handler import AIInsights
from auth_handler import (
    create_user_table, add_user, authenticate_user,
    get_all_users, delete_user, change_user_role
)

# API Keys
ALPHA_VANTAGE_KEY = "WPKRZRI7UK096O5E"
GOOGLE_API_KEY = "AIzaSyAIFQijh_mCe9tyU70jY8M_d--pAh8Ux9A"

# Init user table
create_user_table()

# Session state setup
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.page = "login"

# UI Pages
def login_page():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        success, role = authenticate_user(username, password)
        if success:
            st.success("Login successful!")
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role
            st.session_state.page = "dashboard"
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.markdown("Don't have an account? [Register below](#register)")
    st.markdown("---")
    if st.button("Go to Register"):
        st.session_state.page = "register"
        st.rerun()

def register_page():
    st.title("📝 Register")
    username = st.text_input("Create Username")
    password = st.text_input("Create Password", type="password")

    if st.button("Register"):
        try:
            add_user(username, password)
            st.success("Registered successfully! Please login.")
            st.session_state.page = "login"
            st.rerun()
        except ValueError as ve:
            st.error(str(ve))

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

def logout():
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.page = "login"
    st.rerun()

def admin_panel():
    st.subheader("👮 Admin Dashboard")
    users = get_all_users()
    for user in users:
        uid, uname, role = user
        cols = st.columns([3, 2, 2, 1])
        cols[0].markdown(f"**{uname}**")
        cols[1].markdown(f"Role: `{role}`")
        if uname != st.session_state.username:
            if cols[2].button(f"Delete {uname}", key=f"del_{uid}"):
                delete_user(uname)
                st.rerun()

def dashboard_page():
    st.title("📈 Stock AI Dashboard")

    ticker = st.text_input("Enter Stock Ticker", value="RELIANCE")
    market = st.selectbox("Select Market", ["BSE", "NASDAQ"])
    image_path = f"D:/Bollinger_analysis/images/{market}_{ticker}.png"

    if st.button("Analyze Stock"):
        st.session_state.image_path = image_path

        with st.spinner("Fetching and analyzing stock data..."):
            stock_api = StockAPI(ALPHA_VANTAGE_KEY)
            stock_data = stock_api.get_stock_info(ticker, market)
            analyzer = StockAnalyzer()
            df = analyzer.json_to_dataframe(stock_data, ticker, market)
            analyzer.plot_stock_data(df, ticker, market, image_path)

            ai = AIInsights()
            response = ai.get_ai_insights(image_path, ticker, market)

            insights = ""
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    insights += part.text

            st.session_state.ai_insights = insights
            st.session_state.df = df

        st.success("Analysis complete!")

    if st.session_state.get("df") is not None:
        st.image(st.session_state.image_path, use_column_width=True)
        st.subheader("AI Insights")
        st.write(st.session_state.ai_insights)

# Router
if st.session_state.page == "login":
    login_page()

elif st.session_state.page == "register":
    register_page()

elif st.session_state.page == "dashboard":
    col1, col2 = st.columns([6, 1])
    col1.markdown(f"👤 Logged in as `{st.session_state.username}`")
    col2.button("Logout", on_click=logout)

    if st.session_state.role == "admin":
        with st.expander("Admin Tools"):
            admin_panel()

    dashboard_page()
