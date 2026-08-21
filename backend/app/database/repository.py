import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("backend.repository")


class AirQualityRepository:
    """Database access methods for air quality measurements."""

    @staticmethod
    def get_daily_summary(
        session: Session,
        city: str = "Coimbatore",
        parameter: str = "pm25",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch daily average concentration and max AQI for a given city and pollutant parameter."""
        sql = text("""
            SELECT 
                TO_CHAR(reading_timestamp, 'YYYY-MM-DD') AS reading_date,
                ROUND(AVG(normalized_value)::numeric, 2) AS avg_concentration,
                MAX(aqi_us_epa) AS max_aqi
            FROM air_quality_readings
            WHERE LOWER(city) = LOWER(:city)
              AND LOWER(parameter) = LOWER(:parameter)
              AND (:start_date IS NULL OR reading_timestamp >= :start_date_ts)
              AND (:end_date IS NULL OR reading_timestamp <= :end_date_ts)
            GROUP BY TO_CHAR(reading_timestamp, 'YYYY-MM-DD')
            ORDER BY reading_date ASC;
        """)

        start_date_ts = f"{start_date}T00:00:00Z" if start_date else None
        end_date_ts = f"{end_date}T23:59:59Z" if end_date else None

        params = {
            "city": city,
            "parameter": parameter,
            "start_date": start_date,
            "start_date_ts": start_date_ts,
            "end_date": end_date,
            "end_date_ts": end_date_ts,
        }

        result = session.execute(sql, params)
        rows = result.mappings().all()

        return [
            {
                "date": row["reading_date"],
                "avg_concentration": float(row["avg_concentration"]) if row["avg_concentration"] is not None else 0.0,
                "max_aqi": int(row["max_aqi"]) if row["max_aqi"] is not None else None,
            }
            for row in rows
        ]


class EarthquakeRepository:
    """Database access methods for earthquake hazards data."""

    @staticmethod
    def get_events(
        session: Session,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_magnitude: Optional[float] = None,
        max_magnitude: Optional[float] = None,
        region: Optional[str] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Fetch earthquake events filtered by date range, magnitude range, and region."""
        sql = text("""
            SELECT 
                event_id,
                TO_CHAR(event_time, 'YYYY-MM-THH24:MI:SS"Z"') AS event_time,
                magnitude,
                magnitude_category,
                place,
                region,
                latitude,
                longitude,
                depth_km,
                tsunami
            FROM earthquake_events
            WHERE (:start_date IS NULL OR event_time >= :start_date_ts)
              AND (:end_date IS NULL OR event_time <= :end_date_ts)
              AND (:min_mag IS NULL OR magnitude >= :min_mag)
              AND (:max_mag IS NULL OR magnitude <= :max_mag)
              AND (:region IS NULL OR LOWER(region) LIKE LOWER(:region_like))
            ORDER BY event_time DESC
            LIMIT :limit;
        """)

        start_date_ts = f"{start_date}T00:00:00Z" if start_date else None
        end_date_ts = f"{end_date}T23:59:59Z" if end_date else None
        region_like = f"%{region}%" if region else None

        params = {
            "start_date": start_date,
            "start_date_ts": start_date_ts,
            "end_date": end_date,
            "end_date_ts": end_date_ts,
            "min_mag": min_magnitude,
            "max_mag": max_magnitude,
            "region": region,
            "region_like": region_like,
            "limit": limit,
        }

        result = session.execute(sql, params)
        rows = result.mappings().all()

        return [
            {
                "event_id": str(row["event_id"]),
                "event_time": str(row["event_time"]),
                "magnitude": float(row["magnitude"]),
                "magnitude_category": str(row["magnitude_category"]),
                "place": str(row["place"]) if row["place"] else None,
                "region": str(row["region"]) if row["region"] else None,
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "depth_km": float(row["depth_km"]),
                "tsunami": int(row["tsunami"]) if row["tsunami"] else 0,
            }
            for row in rows
        ]

    @staticmethod
    def get_regional_summary(session: Session) -> List[Dict[str, Any]]:
        """Fetch regional seismic event count, max magnitude, avg depth, and tsunami alert summary."""
        sql = text("""
            SELECT 
                region,
                COUNT(*) AS total_events,
                MAX(magnitude) AS max_magnitude,
                ROUND(AVG(depth_km)::numeric, 2) AS avg_depth_km,
                SUM(tsunami) AS tsunami_alerts
            FROM earthquake_events
            GROUP BY region
            ORDER BY total_events DESC;
        """)
        result = session.execute(sql)
        rows = result.mappings().all()

        return [
            {
                "region": str(row["region"] or "Unknown Region"),
                "total_events": int(row["total_events"]),
                "max_magnitude": float(row["max_magnitude"]),
                "avg_depth_km": float(row["avg_depth_km"]) if row["avg_depth_km"] is not None else 0.0,
                "tsunami_alerts": int(row["tsunami_alerts"] or 0),
            }
            for row in rows
        ]

    @staticmethod
    def get_monthly_categories(session: Session) -> List[Dict[str, Any]]:
        """Fetch monthly breakdown of earthquakes by analytical magnitude category."""
        sql = text("""
            SELECT 
                TO_CHAR(event_time, 'YYYY-MM') AS month,
                magnitude_category,
                COUNT(*) AS event_count
            FROM earthquake_events
            GROUP BY month, magnitude_category
            ORDER BY month DESC;
        """)
        result = session.execute(sql)
        rows = result.mappings().all()

        return [
            {
                "month": str(row["month"]),
                "magnitude_category": str(row["magnitude_category"]),
                "event_count": int(row["event_count"]),
            }
            for row in rows
        ]


class AnalyticsRepository:
    """Database access methods for independent time-series analytics trends."""

    @staticmethod
    def get_independent_trends(
        session: Session,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch independent daily PM2.5 average concentration and daily earthquake counts."""
        sql = text("""
            WITH dates AS (
                SELECT generate_series(
                    COALESCE(:start_date::date, CURRENT_DATE - INTERVAL '30 days'),
                    COALESCE(:end_date::date, CURRENT_DATE),
                    '1 day'::interval
                )::date AS d
            ),
            aq AS (
                SELECT DATE(reading_timestamp) AS d, ROUND(AVG(normalized_value)::numeric, 2) AS pm25_avg
                FROM air_quality_readings
                WHERE LOWER(parameter) IN ('pm25', 'pm2.5')
                GROUP BY DATE(reading_timestamp)
            ),
            eq AS (
                SELECT DATE(event_time) AS d, COUNT(*) AS eq_count
                FROM earthquake_events
                GROUP BY DATE(event_time)
            )
            SELECT 
                dates.d::text AS date,
                aq.pm25_avg,
                COALESCE(eq.eq_count, 0) AS earthquake_count
            FROM dates
            LEFT JOIN aq ON dates.d = aq.d
            LEFT JOIN eq ON dates.d = eq.d
            ORDER BY dates.d ASC;
        """)

        params = {
            "start_date": start_date,
            "end_date": end_date,
        }

        result = session.execute(sql, params)
        rows = result.mappings().all()

        return [
            {
                "date": str(row.get("date") or row.get("trend_date") or row.get("d") or ""),
                "pm25_avg": float(row["pm25_avg"]) if row["pm25_avg"] is not None else None,
                "earthquake_count": int(row["earthquake_count"] or 0),
            }
            for row in rows
        ]
