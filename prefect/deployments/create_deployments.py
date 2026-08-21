import os
import sys

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from prefect.flows.openaq_flow import openaq_etl_flow
from prefect.flows.usgs_flow import usgs_etl_flow


def deploy_flows():
    """Build and serve/deploy OpenAQ and USGS Prefect flows."""
    print("Building Prefect Deployments...")

    openaq_deployment = openaq_etl_flow.to_deployment(
        name="openaq-coimbatore-deployment",
        parameters={
            "city": "Coimbatore",
            "latitude": 11.0168,
            "longitude": 76.9558,
            "radius": 25000,
            "measurement_limit": 2000,
        },
        tags=["openaq", "environmental-data"],
    )

    usgs_deployment = usgs_etl_flow.to_deployment(
        name="usgs-earthquake-deployment",
        parameters={
            "start_date": "2026-01-01",
            "end_date": "2026-08-20",
            "min_magnitude": 2.5,
            "limit": 1000,
        },
        tags=["usgs", "earthquakes"],
    )

    print("Deployments constructed successfully!")
    return openaq_deployment, usgs_deployment


if __name__ == "__main__":
    deploy_flows()
