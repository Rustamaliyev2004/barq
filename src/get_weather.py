import pandas as pd, requests, time

# three points covering the German fleet: south solar, centre, north wind
POINTS = [(48.14, 11.58), (51.34, 12.37), (53.08, 8.80)]

VARS = "shortwave_radiation,temperature_2m,cloud_cover,wind_speed_100m"

frames = []
for i, (lat, lon) in enumerate(POINTS):
    print(f"fetching point {i+1}...")
    r = requests.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": lat, "longitude": lon,
            "start_date": "2020-01-01", "end_date": "2024-12-31",
            "hourly": VARS, "timezone": "Europe/Berlin",
        }, timeout=120)
    r.raise_for_status()
    h = r.json()["hourly"]
    df = pd.DataFrame(h)
    df["ts"] = pd.to_datetime(df.pop("time"))
    frames.append(df.set_index("ts"))
    time.sleep(2)

wx = sum(frames) / len(frames)
wx.to_parquet("data/de_weather.parquet")
print(wx.shape)
print(wx.head())
print(wx.isna().sum())