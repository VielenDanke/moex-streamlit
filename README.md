# 📈 MOEX Trading Dashboard

This is a Streamlit web application designed to visualize trading data stored in an Apache Cassandra database. It provides real-time insights into market activities, including hourly trading volumes and raw trade logs.

## ✨ Features

* **Hourly Aggregation:** Visualizes total trading volume per security over hourly windows using interactive bar charts.
* **Real-time Trades:** Displays raw trade data in tabular format with an interactive scatter plot showing price dynamics over time.
* **Smart Filtering:** Allows filtering by security (Ticker) to focus on specific assets (e.g., SBER, GAZP).
* **Auto-refresh:** Includes buttons to refresh data on demand without reloading the page.
* **Docker Ready:** Fully containerized for easy deployment.

## 🛠️ Prerequisites

* **Python 3.9+**
* **Apache Cassandra:** A running instance with the `moex` keyspace and relevant tables (`iss_data`, `iss_data_hourly_volume`).
* **Network:** Access to the Cassandra port (default `9042`).

## 📦 Installation

1.  **Clone the repository** to your local machine.

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install streamlit pandas plotly cassandra-driver
    ```

## ⚙️ Environment Setup

The application uses environment variables to connect to the Cassandra database. You can set these in your terminal or use a `.env` file.

| Variable | Required | Default | Description |
| :--- | :---: | :--- | :--- |
| `CASSANDRA_HOSTS` | ✅ Yes | `localhost` | Comma-separated list of Cassandra host IPs (e.g., `127.0.0.1,192.168.1.5`). |
| `CASSANDRA_PORT` | No | `9042` | Port for the Cassandra native transport. |
| `KEYSPACE` | No | `moex` | The keyspace name to query data from. |

### Configuration Examples

**Linux/macOS:**

```bash
export CASSANDRA_HOSTS="localhost"
export CASSANDRA_PORT="9042"
export KEYSPACE="moex"