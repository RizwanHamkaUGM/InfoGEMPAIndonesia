import os
import time
import pandas as pd
import requests
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# Autentikasi Google Sheets
def authenticate_google_sheets():
    # Define the Google Sheets API scope
    scope = ['https://www.googleapis.com/auth/spreadsheets']

    # Fetch the credential JSON string from the environment variable
    cred_json = os.environ.get("CREDENTIALS_API")
    if not cred_json:
        raise ValueError("Environment variable 'CREDENTIALS_API' is not set or is empty.")

    # Attempt to decode the JSON string to a dictionary
    try:
        creds_dict = json.loads(cred_json)
    except json.JSONDecodeError as e:
        raise ValueError("The 'CREDENTIALS_API' environment variable contains invalid JSON data.") from e

    # Authenticate using the decoded credentials dictionary
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
    except Exception as e:
        raise ValueError("Failed to authenticate with Google Sheets API.") from e

    print("Successfully authenticated with Google Sheets API.")
    return client

# Fungsi untuk mengambil dan memperbarui data dari BMKG ke Google Sheets
def fetch_and_update_data(sheet_url):
    client = authenticate_google_sheets()
    spreadsheet = client.open_by_url(sheet_url)
    sheet = spreadsheet.get_worksheet(0)  # Worksheet pertama

    # Ambil data dari BMKG
    url = 'https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json'
    response = requests.get(url)
    response_data = response.json()
    
    # Normalisasi JSON ke dalam DataFrame
    df = pd.json_normalize(response_data['Infogempa']['gempa'])
    df_relevant = df[['Tanggal', 'Jam', 'Coordinates', 'DateTime', 'Lintang', 'Bujur', 
                      'Magnitude', 'Kedalaman', 'Wilayah', 'Potensi', 'Dirasakan', 'Shakemap']]
    
    # Baca data dari Google Sheets
    existing_data = pd.DataFrame(sheet.get_all_records())
    if not existing_data.empty:
        latest_date_in_file = existing_data['DateTime'].max()
        # Filter data yang lebih baru dari yang sudah ada di Google Sheets
        df_relevant = df_relevant[df_relevant['DateTime'] > latest_date_in_file]

    # Jika ada data baru, tambahkan ke Google Sheets
    if not df_relevant.empty:
        sheet.append_rows(df_relevant.values.tolist())
        print("Data terbaru berhasil ditambahkan ke Google Sheets.")
        create_map()
        create_UI()
        up_to_instagram()
    else:
        print("Data sudah up-to-date. Tidak ada data baru.")

# Path Google Sheets kamu
sheet_url = 'https://docs.google.com/spreadsheets/d/1yoEq7eaVEOivxJyH8JjtHDAgHlE1qOnmuZIij2AxYJc/edit?usp=sharing'  # Ganti dengan URL Google Sheets kamu

def create_map():
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

    # Fungsi untuk konversi lintang dan bujur dari format teks ke float
    def convert_coordinates(lintang, bujur):
        if 'LS' in lintang:
            latitude = -float(lintang.replace('LS', '').strip())
        elif 'LU' in lintang:
            latitude = float(lintang.replace('LU', '').strip())
        if 'BT' in bujur:
            longitude = float(bujur.replace('BT', '').strip())
        elif 'BB' in bujur:
            longitude = -float(bujur.replace('BB', '').strip())
        return latitude, longitude

    def read_data_from_sheets(sheet_url):
        # Autentikasi dan buka sheet berdasarkan URL
        client = authenticate_google_sheets()
        spreadsheet = client.open_by_url(sheet_url)
        sheet = spreadsheet.get_worksheet(0)  # worksheet pertama

        # Mendapatkan data dari Google Sheets sebagai DataFrame
        records = sheet.get_all_records()
        df = pd.DataFrame(records)

        # Mendapatkan data terbaru berdasarkan DateTime yang paling akhir
        latest_data = df.sort_values('DateTime', ascending=False).iloc[0]
        return {
            "tanggal": latest_data['Tanggal'],
            "waktu": latest_data['Jam'],
            "koordinat": latest_data['Coordinates'],
            "lintang": latest_data['Lintang'],
            "bujur": latest_data['Bujur'],
            "magnitude": latest_data['Magnitude'],
            "kedalaman": latest_data['Kedalaman'],
            "wilayah": latest_data['Wilayah'],
            'potensi': latest_data['Potensi']
        }

    # Contoh penggunaan
    data = read_data_from_sheets(sheet_url)
    
    latitude, longitude = convert_coordinates(data['lintang'], data['bujur'])
    
    fig = plt.figure(figsize=(9, 18))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([94, 141, -15, 12], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND, color='lightgray')
    ax.add_feature(cfeature.OCEAN, color='#25656a')
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')

    ax.plot(longitude, latitude, 'ro', markersize=4, transform=ccrs.PlateCarree(), label="Lokasi Gempa")
    num_rings = 10
    ring_spacing = 0.7
    for i in range(1, num_rings + 1):
        circle_radius = i * ring_spacing
        circle = plt.Circle((longitude, latitude), circle_radius, color='red', fill=False, linestyle='--', transform=ccrs.PlateCarree())
        ax.add_patch(circle)
    
    plt.savefig(os.path.join("InfoGempaID_CSV", "lokasi_baru1.png"), bbox_inches='tight', pad_inches=0)
    print("Map tersimpan sebagai 'lokasi_baru1.png'.")

def create_UI():
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    def read_data_from_sheets(sheet_url):
        # Autentikasi dan buka sheet berdasarkan URL
        client = authenticate_google_sheets()
        spreadsheet = client.open_by_url(sheet_url)
        sheet = spreadsheet.get_worksheet(0)  # worksheet pertama

        # Mendapatkan data dari Google Sheets sebagai DataFrame
        records = sheet.get_all_records()
        df = pd.DataFrame(records)

        # Mendapatkan data terbaru berdasarkan DateTime yang paling akhir
        latest_data = df.sort_values('DateTime', ascending=False).iloc[0]
        return {
            "tanggal": latest_data['Tanggal'],
            "waktu": latest_data['Jam'],
            "koordinat": latest_data['Coordinates'],
            "lintang": latest_data['Lintang'],
            "bujur": latest_data['Bujur'],
            "magnitude": latest_data['Magnitude'],
            "kedalaman": latest_data['Kedalaman'],
            "wilayah": latest_data['Wilayah'],
            'potensi': latest_data['Potensi']
        }

    # Contoh penggunaan

    def wrap_text(text, line_length=40):
        return textwrap.wrap(text, width=line_length)

    def create_earthquake_image(data, template_path, output_path, map_path):
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)
        map_img = Image.open(map_path).resize((975, 575), Image.LANCZOS)
        img.paste(map_img, (50, 130))
        font_path = os.path.join("fonts", "HelveticaNowDisplay-Regular.ttf")
        font_bold = os.path.join("fonts", "HelveticaNowDisplay-Bold.ttf")
        font_small = ImageFont.truetype(font_path, 22)
        font_intermediate = ImageFont.truetype(font_bold, 22)
        font_large = ImageFont.truetype(font_bold, 180)

        draw.text((70, 765), data['tanggal'], font=font_small, fill="black")
        draw.text((70, 865), data['waktu'], font=font_small, fill="black")
        draw.text((70, 965), data['koordinat'], font=font_small, fill="black")
        wilayah_lines = wrap_text(data['wilayah'], line_length=40)
        y_pos = 765
        for line in wilayah_lines:
            draw.text((285, y_pos), line, font=font_small, fill="black")
            y_pos += 25
        draw.text((285, 865), data['kedalaman'], font=font_small, fill="black")
        draw.text((285, 965), data['bujur'], font=font_small, fill="black")
        draw.text((505, 965), data['lintang'], font=font_small, fill="black")
        draw.text((760, 765), str(data['magnitude']), font=font_large, fill="black")
        potensi_lines = wrap_text(data['potensi'], line_length=30)
        y_pos = 945
        for line in potensi_lines:
            draw.text((760, y_pos), line, font=font_intermediate, fill="red")
            y_pos += 25

        img.save(output_path)
        print(f"Gambar disimpan di {output_path}")

    data = read_data_from_sheets(sheet_url)
    template_path = os.path.join("InfoGempaID_CSV", "UiGempaTanpaMap.png")
    output_path = os.path.join("InfoGempaID_CSV", "GEMPATERBARU.png")
    map_path = os.path.join("InfoGempaID_CSV", "lokasi_baru1.png")

    if data:
        create_earthquake_image(data, template_path, output_path, map_path)

def up_to_instagram():
    from instagrapi import Client

    def read_data_from_sheets(sheet_url):
        # Autentikasi dan buka sheet berdasarkan URL
        client = authenticate_google_sheets()
        spreadsheet = client.open_by_url(sheet_url)
        sheet = spreadsheet.get_worksheet(0)  # worksheet pertama

        # Mendapatkan data dari Google Sheets sebagai DataFrame
        records = sheet.get_all_records()
        df = pd.DataFrame(records)

        # Mendapatkan data terbaru berdasarkan DateTime yang paling akhir
        latest_data = df.sort_values('DateTime', ascending=False).iloc[0]
        return {
            "tanggal": latest_data['Tanggal'],
            "waktu": latest_data['Jam'],
            "koordinat": latest_data['Coordinates'],
            "lintang": latest_data['Lintang'],
            "bujur": latest_data['Bujur'],
            "magnitude": latest_data['Magnitude'],
            "kedalaman": latest_data['Kedalaman'],
            "wilayah": latest_data['Wilayah'],
            'potensi': latest_data['Potensi']
        }

    # Contoh penggunaan
    data = read_data_from_sheets(sheet_url)

    capt = (f"🌍 Gempa Terkini ! 🌍\n\n📍  Lokasi     : {data['wilayah']}\n📅  Tanggal   : {data['tanggal']}\n"
            f"🕗  Waktu     : {data['waktu']}\n🎯  Koordinat : {data['koordinat']}\n"
            f"📊  Magnitudo : {data['magnitude']} SR\n📏  Kedalaman : {data['kedalaman']}\n"
            f"📢  Potensi   : {data['potensi']}\n#Gempa #Kesiapsiagaan #Indonesia #InfoIDGempa #MitigasiBencana #SiagaBencana #KesiapsiagaanGempa #GempaBumi #IndonesiaTangguh #InfoGempaTerkini #GempaTerkini #UpdateGempa #PerlindunganDiri #Kebencanaan #Earthquake #EarthquakePreparedness\n\nData resmi dari BMKG.")

    cl = Client()
    cl.login("infogempaid", "Minimode12")
    media_path = os.path.join("InfoGempaID_CSV", "GEMPATERBARU.png")
    cl.photo_upload(media_path, capt)
    print("Post berhasil diunggah ke Instagram.")

# Eksekusi proses utama
fetch_and_update_data(sheet_url)
