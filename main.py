from datetime import datetime
import json
import re
import pandas as pd
import pytz
import requests

SHEET_URL = "https://docs.google.com/spreadsheets/d/1ldoiUSfjZ9-e9SJA7Hy8Y6xuA16d1sWmciO1l5qyXfQ/export?format=csv&gid=0"
HIDROLOGI_URL = "https://hidrologi.id/portal/curah-hujan"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/115.0.0.0 Safari/537.36"
    )
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

        matches = re.findall(
            r"var\s+dataPos\s*=\s*(\[.*?\]);", res.text, re.DOTALL
        )
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
                        "Lintang": item.get("latitude", None),
                        "Bujur": item.get("longitude", None),
                        "CH": item.get("curah_hujan", 0),
                    }
                )
            return pd.DataFrame(rows)
        return pd.DataFrame()
    except Exception as e:
        print(f"Gagal Hidrologi: {e}")
        return pd.DataFrame()


def main():
    # 1. Dapatkan Tanggal Hari Ini (WITA / Asia/Makassar)
    wita_tz = pytz.timezone("Asia/Makassar")
    now = datetime.now(wita_tz)

    tanggal_str = now.strftime("%Y-%m-%d")  # Contoh: 2026-10-15
    waktu_lengkap = now.strftime("%Y-%m-%d %H:%M:%S")

    # 2. Tarik Data
    df_sheet = fetch_google_sheet(SHEET_URL)
    df_hidro = fetch_hidrologi_data(HIDROLOGI_URL)

    # 3. Gabungkan Data
    df_gabungan = pd.concat([df_sheet, df_hidro], ignore_index=True)

    # 4. Tambahkan Tanggal Update
    df_gabungan["Tanggal_Update"] = waktu_lengkap

    # 5. Susun Kolom Target
    kolom_target = [
        "No",
        "Provinsi",
        "Kabupaten",
        "Kecamatan",
        "Nama_Pos",
        "Lintang",
        "Bujur",
        "CH",
        "Tanggal_Update",
    ]
    for col in kolom_target:
        if col not in df_gabungan.columns:
            df_gabungan[col] = None

    df_gabungan = df_gabungan.dropna(how="all")
    df_gabungan = df_gabungan[kolom_target]
    df_gabungan["No"] = range(1, len(df_gabungan) + 1)

    # 6. Simpan ke File CSV Baru Sesuai Tanggal (misal: 9_2026-10-15.csv)
    nama_file_baru = f"9_{tanggal_str}.csv"
    df_gabungan.to_csv(nama_file_baru, index=False)

    # Tetap simpan juga ke 9.csv sebagai master/file data paling terbaru
    df_gabungan.to_csv("9.csv", index=False)

    print(
        f"Berhasil membuat file baru '{nama_file_baru}' dan memperbarui '9.csv' pada {waktu_lengkap}"
    )


if __name__ == "__main__":
    main()
