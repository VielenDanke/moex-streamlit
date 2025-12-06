from os import environ

import pandas as pd
import plotly.express as px
import streamlit as st
from cassandra.cluster import Cluster

# --- Configuration ---
# Adjust these if your Docker setup uses different ports or auth
CASSANDRA_HOSTS = environ.get("CASSANDRA_HOSTS").split(",")
CASSANDRA_PORT = environ.get("CASSANDRA_PORT")
KEYSPACE = environ.get("KEYSPACE")

# If you have authentication enabled in Cassandra (e.g. SASL_PLAINTEXT)
# AUTH_PROVIDER = PlainTextAuthProvider(username='admin', password='admin-password')
AUTH_PROVIDER = None

# Page Config
st.set_page_config(
    page_title="MOEX Trading Dashboard",
    page_icon="📈",
    layout="wide"
)


# --- Cassandra Connection ---
@st.cache_resource
def get_cluster():
    """Singleton connection to Cassandra"""
    cluster = Cluster(
        contact_points=CASSANDRA_HOSTS,
        port=CASSANDRA_PORT,
        auth_provider=AUTH_PROVIDER
    )
    return cluster


def get_session():
    cluster = get_cluster()
    session = cluster.connect()
    return session


# --- Data Fetching ---
@st.cache_data(ttl=60)  # Cache data for 60 seconds
def fetch_hourly_volume():
    """
    Fetches aggregated hourly volume data.
    Corresponds to Chart 1 in your request.
    Table: iss_data_hourly_volume
    """
    session = get_session()
    # We use ALLOW FILTERING strictly for demo purposes if partition keys aren't specified.
    # In prod, you should filter by date/secid.
    query = f"SELECT secid, window_start, total_volume FROM {KEYSPACE}.iss_data_hourly_volume"

    try:
        rows = session.execute(query)
        return pd.DataFrame(list(rows))
    except Exception as e:
        st.error(f"Error fetching hourly volume: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=10)  # Refresh raw trades often
def fetch_raw_trades(limit=1000):
    """
    Fetches raw trade data.
    Corresponds to Chart 2 in your request.
    Table: iss_data
    """
    session = get_session()
    query = f"SELECT secid, tradetime, price, quantity, value, boardid FROM {KEYSPACE}.iss_data LIMIT {limit}"

    try:
        rows = session.execute(query)
        return pd.DataFrame(list(rows))
    except Exception as e:
        st.error(f"Error fetching raw trades: {e}")
        return pd.DataFrame()


# --- Main App Layout ---
st.title("📈 MOEX Data Analytics")
st.markdown(f"Connected to Cassandra at `{CASSANDRA_HOSTS[0]}:{CASSANDRA_PORT}` | Keyspace: `{KEYSPACE}`")

# Create tabs for different views
tab1, tab2 = st.tabs(["📊 Hourly Aggregation", "⚡ Real-time Trades"])

# --- Tab 1: Aggregated Volume ---
with tab1:
    st.header("Hourly Trading Volume by Security")

    df_volume = fetch_hourly_volume()

    if not df_volume.empty:
        # Ensure correct data types
        df_volume['window_start'] = pd.to_datetime(df_volume['window_start'])
        df_volume['total_volume'] = df_volume['total_volume'].astype(float)

        # Filters
        all_secids = df_volume['secid'].unique().tolist()
        selected_secids = st.multiselect("Filter by Security (Ticker)", all_secids, default=all_secids[:5])

        if selected_secids:
            filtered_vol = df_volume[df_volume['secid'].isin(selected_secids)]

            # Plotly Bar Chart
            fig_vol = px.bar(
                filtered_vol,
                x="window_start",
                y="total_volume",
                color="secid",
                title="Total Volume per Hour",
                labels={"window_start": "Time Window", "total_volume": "Volume (Currency)"},
                barmode='group'
            )
            st.plotly_chart(fig_vol, use_container_width=True)

            # Data Table
            with st.expander("View Raw Aggregated Data"):
                st.dataframe(filtered_vol.sort_values(by='window_start', ascending=False))
        else:
            st.info("Please select at least one security.")
    else:
        st.warning("No data found in 'iss_data_hourly_volume'. Ensure your Spark job has run successfully.")

# --- Tab 2: Raw Trades ---
with tab2:
    st.header("Recent Market Trades")

    # Refresh button
    if st.button("Refresh Trades"):
        fetch_raw_trades.clear()

    df_trades = fetch_raw_trades()

    if not df_trades.empty:
        # Ensure correct data types
        df_trades['tradetime'] = pd.to_datetime(df_trades['tradetime'])

        # Interactive Scatter Plot: Time vs Price
        st.subheader("Price Dynamics")

        # Filter for top traded assets to avoid clutter
        top_assets = df_trades['secid'].value_counts().head(5).index.tolist()
        df_trades_filtered = df_trades[df_trades['secid'].isin(top_assets)]

        fig_price = px.scatter(
            df_trades_filtered,
            x="tradetime",
            y="price",
            color="secid",
            size="quantity",
            hover_data=["boardid", "value"],
            title="Price vs Time (Top 5 Active Securities)",
            labels={"tradetime": "Trade Time", "price": "Price"}
        )
        st.plotly_chart(fig_price, use_container_width=True)

        # Metrics Row
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Trades Loaded", len(df_trades))
        col2.metric("Total Value Traded", f"{df_trades['value'].sum():,.2f}")
        col3.metric("Active Tickers", df_trades['secid'].nunique())

        # Raw Data Table
        st.subheader("Trade Log")
        st.dataframe(df_trades.sort_values(by='tradetime', ascending=False), use_container_width=True)
    else:
        st.warning("No data found in 'iss_data'. Ensure your Kafka->Cassandra pipeline is running.")
