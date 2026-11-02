import os
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from streamlit_autorefresh import st_autorefresh


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Ride Analytics | Azure",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:5000")
PROMETHEUS_URL = os.getenv(
    "PROMETHEUS_URL",
    "http://prometheus.rideanalytics.svc.cluster.local:9090"
    if os.getenv("KUBERNETES_SERVICE_HOST")
    else "http://127.0.0.1:9090"
)
REFRESH_INTERVAL = 5000


# ==================================================
# 2. AUTOMATIC DASHBOARD REFRESH
# ==================================================

st_autorefresh(
    interval=REFRESH_INTERVAL,
    key="ride_dashboard_refresh"
)


# ==================================================
# 3. FETCH ANALYTICS FROM FLASK API
# ==================================================

@st.cache_data(ttl=5)
def fetch_analytics():

    response = requests.get(
        f"{API_BASE_URL}/analytics",
        timeout=5
    )

    response.raise_for_status()

    return response.json()


# ==================================================
# 4. LOAD APPLICATION DATA
# ==================================================

try:

    analytics = fetch_analytics()
    api_connected = True
    api_error = None

except requests.exceptions.RequestException as error:

    analytics = None
    api_connected = False
    api_error = str(error)


# ==================================================
# 5. DASHBOARD STYLING
# ==================================================

st.markdown("""
<style>
    :root {
        --ride-blue: #2563eb;
        --ride-blue-dark: #173b73;
        --ride-surface: #ffffff;
        --ride-muted: #64748b;
    }

    .stApp {
        background: #f5f7fb;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.4rem;
        padding-bottom: 2.5rem;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5eaf2;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.4rem;
    }

    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding: 0.38rem 0.55rem;
        border-radius: 0.55rem;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e6ebf3;
        border-radius: 14px;
        padding: 17px 18px;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.035);
    }

    [data-testid="stMetricLabel"] {
        color: #64748b;
        font-size: 0.86rem;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: #172b4d;
        font-weight: 700;
    }

    div[data-testid="stVerticalBlock"] div[data-testid="stPlotlyChart"],
    div[data-testid="stDataFrame"] {
        background: #ffffff;
        border: 1px solid #e6ebf3;
        border-radius: 13px;
        padding: 0.25rem;
    }

    h1, h2, h3 {
        color: #172b4d;
        letter-spacing: -0.025em;
    }

    .ride-brand {
        color: #173b73;
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin-bottom: 0.1rem;
    }

    .ride-subtitle {
        color: #64748b;
        font-size: 0.84rem;
        margin-bottom: 1.3rem;
    }

    .page-eyebrow {
        color: #2563eb;
        font-size: 0.76rem;
        font-weight: 750;
        letter-spacing: 0.11em;
        text-transform: uppercase;
        margin-bottom: 0.25rem;
    }

    .page-description {
        color: #64748b;
        font-size: 0.96rem;
        margin-top: -0.45rem;
        margin-bottom: 1.25rem;
    }

    .section-heading {
        color: #243b5a;
        font-size: 1.08rem;
        font-weight: 700;
        margin: 0.4rem 0 0.7rem 0;
    }

    hr {
        border-color: #e5eaf2 !important;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)


# ==================================================
# 6. SIDEBAR NAVIGATION
# ==================================================

with st.sidebar:

    st.markdown('<div class="ride-brand">🚗 RideOps</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="ride-subtitle">TRANSPORT INTELLIGENCE PLATFORM</div>',
        unsafe_allow_html=True
    )

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "Ride Analytics",
            "Revenue",
            "City Insights",
            "Observability"
        ]
    )

    st.divider()

    if api_connected:

        st.success("Data source: Flask REST API")

        st.caption("Storage: SQLite database")

        st.caption("Auto-refresh: Every 5 seconds")

    else:

        st.error("API connection unavailable")


# ==================================================
# 7. MAIN HEADER
# ==================================================

header_left, header_right = st.columns([4, 1])
with header_left:
    st.markdown('<div class="page-eyebrow">RIDEOPS · ANALYTICS WORKSPACE</div>', unsafe_allow_html=True)
    st.title("Transportation Analytics")
    st.markdown(
        '<div class="page-description">Event-driven ride insights and platform operations</div>',
        unsafe_allow_html=True
    )
with header_right:
    st.caption("LIVE · AUTO REFRESH")
    st.markdown("**Every 5 seconds**")


if not api_connected:

    st.error(
        "Unable to connect to the Flask API."
    )

    st.warning(
        "Make sure the Flask server is running on port 5000."
    )

    st.code(
        "python -m src.api.app",
        language="powershell"
    )

    with st.expander("Connection details"):

        st.write(api_error)

    st.stop()


st.success("Connected to Flask REST API")

st.caption(
    "Analytics retrieved from SQLite through Flask REST API."
)


# ==================================================
# 8. EXTRACT ANALYTICS
# ==================================================

total_rides = analytics.get("total_rides", 0)

completed_rides = analytics.get("completed_rides", 0)

booked_rides = analytics.get("booked_rides", 0)

cancelled_rides = analytics.get("cancelled_rides", 0)

total_revenue = analytics.get("total_revenue", 0)

cancellation_rate = analytics.get("cancellation_rate", 0)

city_data = analytics.get("city_wise", [])


city_df = pd.DataFrame(city_data)


if city_df.empty:

    city_df = pd.DataFrame(
        columns=["city", "total_rides", "revenue"]
    )


# ==================================================
# 9. DERIVED METRICS
# ==================================================

average_fare = (
    total_revenue / completed_rides
    if completed_rides > 0
    else 0
)


status_df = pd.DataFrame({

    "Status": [
        "Completed",
        "Booked",
        "Cancelled"
    ],

    "Rides": [
        completed_rides,
        booked_rides,
        cancelled_rides
    ]

})


# ==================================================
# 10. METRIC SEARCH
# ==================================================

st.subheader("Explore your metrics")

query = st.text_input(
    "Search metrics",
    placeholder=(
        "Try revenue, completed rides, "
        "cancellation rate, Chennai..."
    )
)


metric_catalog = {

    "total rides": [
        "total rides",
        "ride count"
    ],

    "completed rides": [
        "completed rides",
        "successful rides"
    ],

    "booked rides": [
        "booked rides",
        "new bookings"
    ],

    "cancelled rides": [
        "cancelled rides",
        "cancellations"
    ],

    "revenue": [
        "revenue",
        "fare",
        "earnings"
    ],

    "average fare": [
        "average fare",
        "mean fare"
    ],

    "cancellation rate": [
        "cancellation rate",
        "cancel rate"
    ],

    "city-wise analytics": [
        "city",
        "cities",
        "location"
    ]

}


if query.strip():

    q = query.strip().lower()

    matches = [

        metric

        for metric, keywords in metric_catalog.items()

        if q in metric

        or any(
            q in keyword or keyword in q
            for keyword in keywords
        )

    ]

    if not city_df.empty:

        matching_cities = [

            city

            for city in city_df["city"].tolist()

            if q in city.lower()

        ]

        matches.extend(matching_cities)


    if matches:

        st.success(
            "Matching metrics: "
            + " · ".join(matches)
        )

    else:

        st.warning(
            "No matching metric found. "
            "Try revenue, completed rides, "
            "booked rides, cancellations or a city."
        )


# ==================================================
# 11. CITY FILTER
# ==================================================

if not city_df.empty:

    available_cities = sorted(
        city_df["city"].dropna().unique().tolist()
    )

    selected_cities = st.multiselect(
        "Filter city-wise charts",
        available_cities,
        default=available_cities
    )

    filtered_cities = city_df[
        city_df["city"].isin(selected_cities)
    ].copy()

else:

    filtered_cities = city_df


# ==================================================
# 12. OVERVIEW PAGE
# ==================================================

if page == "Overview":

    st.markdown('<div class="page-eyebrow">AT A GLANCE</div>', unsafe_allow_html=True)
    st.subheader("Performance overview")
    st.caption("A live snapshot of ride activity, revenue and service performance.")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total rides",
        f"{total_rides:,}"
    )

    c2.metric(
        "Completed rides",
        f"{completed_rides:,}"
    )

    c3.metric(
        "Revenue",
        f"₹{total_revenue:,.2f}"
    )

    c4.metric(
        "Cancellation rate",
        f"{cancellation_rate:.2f}%"
    )


    left, right = st.columns(2)


    # City-wise ride activity

    with left:

        st.subheader("Ride activity by city")

        if not filtered_cities.empty:

            fig = px.bar(
                filtered_cities,
                x="city",
                y="total_rides",
                color="city",
                labels={
                    "city": "City",
                    "total_rides": "Total rides"
                },
                template="plotly_white"
            )

            st.plotly_chart(
                fig,
                width="stretch"
            )

        else:

            st.info("No city data available.")


    # Ride status breakdown

    with right:

        st.subheader("Ride status breakdown")

        fig = px.pie(
            status_df,
            names="Status",
            values="Rides",
            hole=0.58,
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )


    # City-wise revenue

    st.subheader("City-wise revenue")

    if not filtered_cities.empty:

        fig = px.bar(
            filtered_cities,
            x="city",
            y="revenue",
            color="city",
            labels={
                "city": "City",
                "revenue": "Revenue (₹)"
            },
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )


# ==================================================
# 13. RIDE ANALYTICS PAGE
# ==================================================

elif page == "Ride Analytics":

    st.markdown('<div class="page-eyebrow">TRIP PERFORMANCE</div>', unsafe_allow_html=True)
    st.subheader("Ride analytics")
    st.caption("Understand booking outcomes and completed ride performance.")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Completed rides",
        f"{completed_rides:,}"
    )

    c2.metric(
        "Booked rides",
        f"{booked_rides:,}"
    )

    c3.metric(
        "Cancelled rides",
        f"{cancelled_rides:,}"
    )

    st.metric(
        "Average fare per completed ride",
        f"₹{average_fare:,.2f}"
    )

    st.caption(
        "Average fare = total completed-ride revenue "
        "divided by completed rides."
    )

    st.subheader("Ride status summary")

    st.dataframe(
        status_df,
        width="stretch",
        hide_index=True
    )


# ==================================================
# 14. REVENUE PAGE
# ==================================================

elif page == "Revenue":

    st.markdown('<div class="page-eyebrow">FINANCIAL PERFORMANCE</div>', unsafe_allow_html=True)
    st.subheader("Revenue analysis")
    st.caption("Explore revenue contribution and average fare across cities.")

    st.metric(
        "Total revenue",
        f"₹{total_revenue:,.2f}"
    )

    st.metric(
        "Average fare",
        f"₹{average_fare:,.2f}"
    )

    if not filtered_cities.empty:

        st.subheader("Revenue by city")

        fig = px.bar(
            filtered_cities,
            x="city",
            y="revenue",
            color="city",
            labels={
                "city": "City",
                "revenue": "Revenue (₹)"
            },
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

        st.dataframe(
            filtered_cities,
            width="stretch",
            hide_index=True
        )

    else:

        st.info("No revenue data available.")


# ==================================================
# 15. CITY INSIGHTS PAGE
# ==================================================

elif page == "City Insights":

    st.markdown('<div class="page-eyebrow">GEOGRAPHIC PERFORMANCE</div>', unsafe_allow_html=True)
    st.subheader("City insights")
    st.caption("Compare ride volume and revenue across operating cities.")

    if not filtered_cities.empty:

        st.dataframe(
            filtered_cities,
            width="stretch",
            hide_index=True
        )

        fig = px.bar(
            filtered_cities,
            x="city",
            y="total_rides",
            color="city",
            labels={
                "city": "City",
                "total_rides": "Total rides"
            },
            template="plotly_white"
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

    else:

        st.info("No city data available.")


# ==================================================
# 16. OBSERVABILITY PAGE
# ==================================================

elif page == "Observability":

    st.markdown('<div class="page-eyebrow">PLATFORM HEALTH</div>', unsafe_allow_html=True)
    st.subheader("Observability")
    st.caption("Live application telemetry collected by Prometheus.")

    def query_prometheus(promql):
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=5
        )
        response.raise_for_status()

        payload = response.json()
        if payload.get("status") != "success":
            raise ValueError("Prometheus returned an unsuccessful query.")

        return payload["data"]["result"]

    def metric_value(promql, default=0.0):
        result = query_prometheus(promql)
        if not result:
            return default

        value = float(result[0]["value"][1])
        return value if pd.notna(value) else default

    try:
        total_requests = metric_value(
            "sum(rideanalytics_api_requests_total)"
        )

        average_latency_seconds = metric_value(
            "sum(rate(rideanalytics_api_request_duration_seconds_sum[5m])) "
            "/ "
            "sum(rate(rideanalytics_api_request_duration_seconds_count[5m]))"
        )

        api_error_rate = metric_value(
            '100 * sum(rate(rideanalytics_api_requests_total{http_status=~"5.."}[5m])) '
            "/ "
            "clamp_min(sum(rate(rideanalytics_api_requests_total[5m])), 0.000001)"
        )

        request_rate = metric_value(
            "sum(rate(rideanalytics_api_requests_total[5m]))"
        )

        st.success("Connected to Prometheus")

        metric_columns = st.columns(4)

        metric_columns[0].metric(
            "Total API requests",
            f"{total_requests:,.0f}"
        )
        metric_columns[1].metric(
            "Average API latency",
            f"{average_latency_seconds * 1000:.2f} ms"
        )
        metric_columns[2].metric(
            "API error rate",
            f"{api_error_rate:.2f}%"
        )
        metric_columns[3].metric(
            "API request rate",
            f"{request_rate:.3f} req/sec"
        )

        st.divider()
        st.subheader("API requests by endpoint and status")

        breakdown = query_prometheus(
            "sum by (endpoint, http_status) "
            "(rideanalytics_api_requests_total)"
        )

        if breakdown:
            breakdown_rows = [
                {
                    "Endpoint": item["metric"].get("endpoint", "unknown"),
                    "HTTP status": item["metric"].get("http_status", "unknown"),
                    "Requests": float(item["value"][1])
                }
                for item in breakdown
            ]

            st.dataframe(
                pd.DataFrame(breakdown_rows),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No API request breakdown is available yet.")

        st.caption(
            "Live application metrics are collected by Prometheus from the "
            "RideAnalytics Flask API. The dashboard refreshes every 5 seconds."
        )

        st.info(
            "Event throughput is not displayed yet because the consumer does "
            "not currently export an event-processing metric to Prometheus."
        )

    except (
        requests.exceptions.RequestException,
        ValueError,
        KeyError,
        IndexError,
        TypeError
    ) as error:
        st.error(
            "Unable to retrieve Prometheus metrics. Check that the Prometheus "
            "port-forward is running locally, or that the in-cluster service "
            "is reachable."
        )
        st.caption(str(error))


# ==================================================
# 17. FOOTER
# ==================================================

st.divider()

st.caption(
    "RideOps · Streamlit dashboard · "
    "Flask REST API · SQLite · "
    "Auto-refresh: 5 seconds"
)
