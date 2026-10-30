
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
    page_icon="🚘",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = "http://127.0.0.1:5000"
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

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"] {
        background: var(--secondary-background-color);
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(128,128,128,0.15);
    }

    div[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128,128,128,0.2);
    }

</style>
""", unsafe_allow_html=True)


# ==================================================
# 6. SIDEBAR NAVIGATION
# ==================================================

with st.sidebar:

    st.title("🚘 RideOps")

    st.caption("Azure-based transportation analytics")

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

st.title("Transportation Analytics")

st.caption(
    "Event-driven ride insights and platform operations"
)


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

    st.subheader("Key performance indicators")

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

    st.subheader("Ride analytics")

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

    st.subheader("Revenue analysis")

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

    st.subheader("City-wise insights")

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

    st.subheader("Platform observability")

    st.info(
        "Application telemetry has not been connected yet. "
        "We will populate these metrics after instrumenting "
        "Flask and configuring Prometheus."
    )

    a, b, c = st.columns(3)

    a.metric(
        "API latency",
        "Not connected"
    )

    b.metric(
        "API error rate",
        "Not connected"
    )

    c.metric(
        "Event throughput",
        "Not connected"
    )

    st.caption(
        "Planned integrations: Prometheus, Grafana, "
        "Alertmanager and Microsoft Teams."
    )


# ==================================================
# 17. FOOTER
# ==================================================

st.divider()

st.caption(
    "RideOps · Streamlit dashboard · "
    "Flask REST API · SQLite · "
    "Auto-refresh: 5 seconds"
)
