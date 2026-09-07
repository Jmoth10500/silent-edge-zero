#!/usr/bin/env python3
"""
Collect today's weather for every known GB racecourse and store it.
Real, live, free — run this daily (Section 40, "EARLY MORNING: fetch weather").
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from src.providers.weather_open_meteo import OpenMeteoWeatherProvider

# GB racecourses with coordinates — seed list, expand as courses appear in
# real racecards once The Racing API is connected.
COURSES = {
    "Ascot": (51.4128, -0.6764),
    "Newmarket": (52.2446, 0.3908),
    "Cheltenham": (51.9247, -2.0603),
    "Aintree": (53.4767, -2.9530),
    "Epsom": (51.3160, -0.2560),
    "Goodwood": (50.8874, -0.7396),
    "Doncaster": (53.5228, -1.1288),
    "York": (53.9459, -1.0873),
    "Newbury": (51.3958, -1.3129),
    "Kempton Park": (51.4064, -0.4103),
    "Wolverhampton": (52.5872, -2.1288),
    "Southwell": (53.0611, -0.9569),
    "Lingfield Park": (51.1789, -0.0181),
}


def main():
    conn = psycopg2.connect(dbname="silent_edge_zero")
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO data_source (name, url, free_tier, terms_checked, notes) "
        "VALUES ('open-meteo', 'https://open-meteo.com/', TRUE, %s, 'Live weather, no key, CC BY 4.0 attribution required') "
        "ON CONFLICT (name) DO NOTHING",
        (date.today(),),
    )
    cur.execute("SELECT id FROM data_source WHERE name = 'open-meteo'")
    source_id = cur.fetchone()[0]

    provider = OpenMeteoWeatherProvider()
    today = date.today()
    stored = 0

    for name, (lat, lon) in COURSES.items():
        cur.execute(
            "INSERT INTO course (name, country, latitude, longitude) VALUES (%s, 'GB', %s, %s) "
            "ON CONFLICT (name) DO UPDATE SET latitude = EXCLUDED.latitude, longitude = EXCLUDED.longitude "
            "RETURNING id",
            (name, lat, lon),
        )
        course_id = cur.fetchone()[0]

        try:
            snap = provider.get_snapshot(name, lat, lon, today)
        except Exception as e:
            print(f"  {name}: FAILED — {e}")
            continue

        cur.execute(
            """INSERT INTO weather_snapshot
               (course_id, for_date, rainfall_6h_mm, rainfall_24h_mm, temperature_c,
                wind_speed_kmh, wind_direction_deg, observed_at, available_at, source_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (course_id, snap.for_date, snap.rainfall_6h_mm, snap.rainfall_24h_mm,
             snap.temperature_c, snap.wind_speed_kmh, snap.wind_direction_deg,
             snap.observed_at, snap.available_at, source_id),
        )
        stored += 1
        print(f"  {name}: {snap.temperature_c}°C, wind {snap.wind_speed_kmh}km/h, "
              f"rain 24h {snap.rainfall_24h_mm}mm")

    conn.commit()
    print(f"\nStored {stored}/{len(COURSES)} weather snapshots for {today}.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
