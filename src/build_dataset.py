import pandas as pd, glob

def load(pattern):
    path = glob.glob(f"data/{pattern}")[0]
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)
    ts = pd.to_datetime(df["Start date"], format="%b %d, %Y %I:%M %p")
    df = df.drop(columns=["Start date", "End date"])
    for c in df.columns:
        df[c] = pd.to_numeric(df[c].str.replace(",", "", regex=False), errors="coerce")
    df.index = ts
    return df[~df.index.duplicated(keep="first")]

gen = load("Actual_generation*.csv")
con = load("Actual_consumption*.csv")
pri = load("Day-ahead_prices*.csv")

def pick(df, key, name):
    col = [c for c in df.columns if c.startswith(key)][0]
    return df[[col]].rename(columns={col: name})

power = pd.concat([
    pick(gen, "Wind onshore", "wind"),
    pick(gen, "Photovoltaics", "solar"),
    pick(con, "Residual load", "residual_load"),
    pick(pri, "Germany/Luxembourg", "price"),
], axis=1)

wx = pd.read_parquet("data/de_weather.parquet")
df = power.join(wx, how="inner").dropna()

# time features
df["hour"] = df.index.hour
df["month"] = df.index.month
df["doy"] = df.index.dayofyear

# the curtailment signal: negative prices = too much renewable for the grid
df["curtail"] = (df["price"] < 0).astype(int)

df.to_parquet("data/training.parquet")

print(df.shape)
print(df.head())
print("\nnegative price hours per year:")
print(df.groupby(df.index.year)["curtail"].sum())
print("\nshare of all hours:", round(df["curtail"].mean()*100, 1), "%")