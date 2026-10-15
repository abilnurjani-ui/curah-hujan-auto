import json
import re
import pandas as pd
import requests

SHEET_URL = "https://docs.google.com/spreadsheets/d/1ldoiUSfjZ9-e9SJA7Hy8Y6xuA16d1sWmciO1l5qyXfQ/export?format=csv&gid=0"
HIDROLOGI_URL = "https://hidrologi.id/portal/curah-hujan"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


def fetch_google_sheet(url):
    try:
        return pd.read_csv(url)
    except Exception as e:
        print(f"Gagal Sheet: {e}")
        return pd.DataFrame()


def fetch_hidrologi_data(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        matches = re.findall(r"var\s+dataPos\s*=\s*(\[.*?\]);", res.text, re.DOTALL)
        if not matches:
            matches = re.findall(
                r"JSON\.parse\('(\[.*?\])'\)", res.text, re.DOTALL
            )

        if matches:
            data = json.loads(matches[0])
            rows = []
            for item in data:
                rows.append(
                    {
                        "Provinsi": item.get("provinsi", ""),
                        "Kabupaten": item.get("kabupaten", ""),
                        "Kecamatan": item.get("kecamatan", ""),
                        "Nama_Pos": item.get("nama_pos", ""),
                        "Lintang": float(item.get("latitude", 0)),
                        "Bujur": float(item.get("longitude", 0)),
                        "CH": float(item.get("curah_hujan", 0)),
                    }
                )
            return pd.DataFrame(rows)
        return pd.DataFrame()
    except Exception as e:
        print(f"Gagal Hidrologi: {e}")
        return pd.DataFrame()


def main():
    df_sheet = fetch_google_sheet(SHEET_URL)
    df_hidro = fetch_hidrologi_data(HIDROLOGI_URL)

    df_gabungan = pd.concat([df_sheet, df_hidro], ignore_index=True)

    kolom_target = [
        "No",
        "Provinsi",
        "Kabupaten",
        "Kecamatan",
        "Nama_Pos",
        "Lintang",
        "Bujur",
        "CH",
    ]
    for col in kolom_target:
        if col not in df_gabungan.columns:
            df_gabungan[col] = None

    df_gabungan = df_gabungan.dropna(
        subset=["Nama_Pos", "Lintang", "Bujur"], how="all"
    )
    df_gabungan["No"] = range(1, len(df_gabungan) + 1)
    df_gabungan = df_gabungan[kolom_target]

    df_gabungan.to_csv("9.csv", index=False)
    print("Selesai memperbarui 9.csv")


if __name__ == "__main__":
    main()
