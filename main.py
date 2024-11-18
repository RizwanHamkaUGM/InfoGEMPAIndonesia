import os
import time
import pandas as pd
import requests
import json


# URL CRUD Google Apps Script
BASE_URL = "https://script.google.com/macros/s/AKfycbyKOxOirDv0BFUN_HlaQJpOUqQTUHBY2wck8Fu5TJ6c7PokCnqGC10MfKcoGLekkQXVMw/exec"


# Ambil data dari API BMKG
def fetch_data_from_api():
    url = 'https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json'
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch data from API. HTTP Status: {response.status_code}")
    
    response_data = response.json()
    df = pd.json_normalize(response_data['Infogempa']['gempa'])
    df_relevant = df[['Tanggal', 'Jam', 'Coordinates', 'DateTime', 'Lintang', 'Bujur', 
                      'Magnitude', 'Kedalaman', 'Wilayah', 'Potensi', 'Dirasakan', 'Shakemap']]
    print("Data berhasil diambil dari API BMKG.")
    return df_relevant


# Sinkronisasi data dengan URL CRUD
def sync_data_to_crud(data):
    # Fetch existing data from CRUD
    response = requests.get(BASE_URL, params={"action": "read"})
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch data from CRUD endpoint. HTTP Status: {response.status_code}")
    
    existing_data = pd.DataFrame(response.json())
    if not existing_data.empty:
        latest_date_in_file = existing_data['DateTime'].max()
        data = data[data['DateTime'] > latest_date_in_file]
    
    if not data.empty:
        for _, row in data.iterrows():
            payload = row.to_dict()
            payload["action"] = "create"
            response = requests.post(BASE_URL, json=payload)
            if response.status_code != 200:
                raise ValueError(f"Failed to create new record. HTTP Status: {response.status_code}")
        
        print("Data terbaru berhasil ditambahkan ke CRUD.")
    else:
        print("Tidak ada data baru untuk disinkronkan.")


# Fungsi membuat peta
def create_map():
    import matplotlib.pyplot as plt
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature

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

    def get_latest_data_from_crud():
        response = requests.get(BASE_URL, params={"action": "read"})
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch data from CRUD endpoint. HTTP Status: {response.status_code}")
        
        existing_data = pd.DataFrame(response.json())
        latest_data = existing_data.sort_values('DateTime', ascending=False).iloc[0]
        return latest_data

    data = get_latest_data_from_crud()
    latitude, longitude = convert_coordinates(data['Lintang'], data['Bujur'])
    
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
    
    plt.savefig("lokasi_baru1.png", bbox_inches='tight', pad_inches=0)
    print("Map tersimpan sebagai 'lokasi_baru1.png'.")


# Fungsi membuat UI
def create_UI():
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    def wrap_text(text, line_length=40):
        return textwrap.wrap(text, width=line_length)

    def get_latest_data_from_crud():
        response = requests.get(BASE_URL, params={"action": "read"})
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch data from CRUD endpoint. HTTP Status: {response.status_code}")
        
        existing_data = pd.DataFrame(response.json())
        latest_data = existing_data.sort_values('DateTime', ascending=False).iloc[0]
        return latest_data

    data = get_latest_data_from_crud()
    template_path = "UiGempaTanpaMap.png"
    output_path = "GEMPATERBARU.png"
    map_path = "lokasi_baru1.png"

    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)
    map_img = Image.open(map_path).resize((975, 575), Image.LANCZOS)
    img.paste(map_img, (50, 130))
    font_path = "HelveticaNowDisplay-Regular.ttf"
    font_bold = "HelveticaNowDisplay-Bold.ttf"
    font_small = ImageFont.truetype(font_path, 22)
    font_intermediate = ImageFont.truetype(font_bold, 22)
    font_large = ImageFont.truetype(font_bold, 180)

    draw.text((70, 765), data['Tanggal'], font=font_small, fill="black")
    draw.text((70, 865), data['Jam'], font=font_small, fill="black")
    draw.text((70, 965), data['Coordinates'], font=font_small, fill="black")
    wilayah_lines = wrap_text(data['Wilayah'], line_length=40)
    y_pos = 765
    for line in wilayah_lines:
        draw.text((285, y_pos), line, font=font_small, fill="black")
        y_pos += 25
    draw.text((285, 865), data['Kedalaman'], font=font_small, fill="black")
    draw.text((285, 965), data['Bujur'], font=font_small, fill="black")
    draw.text((505, 965), data['Lintang'], font=font_small, fill="black")
    draw.text((760, 765), str(data['Magnitude']), font=font_large, fill="black")
    potensi_lines = wrap_text(data['Potensi'], line_length=30)
    y_pos = 945
    for line in potensi_lines:
        draw.text((760, y_pos), line, font=font_intermediate, fill="red")
        y_pos += 25

    img.save(output_path)
    print(f"Gambar disimpan di {output_path}")


# Fungsi unggah ke Instagram
def up_to_instagram():
    from instagrapi import Client

    def get_latest_data_from_crud():
        response = requests.get(BASE_URL, params={"action": "read"})
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch data from CRUD endpoint. HTTP Status: {response.status_code}")
        
        existing_data = pd.DataFrame(response.json())
        latest_data = existing_data.sort_values('DateTime', ascending=False).iloc[0]
        return latest_data

    data = get_latest_data_from_crud()

    caption = (f"🌍 Gempa Terkini ! 🌍\n\n📍 Lokasi: {data['Wilayah']}\n📅 Tanggal: {data['Tanggal']}\n"
               f"🕗 Waktu: {data['Jam']}\n🎯 Koordinat: {data['Coordinates']}\n"
               f"📊 Magnitudo: {data['Magnitude']} SR\n📏 Kedalaman: {data['Kedalaman']}\n"
               f"📢 Potensi: {data['Potensi']}\n\n#Gempa #Indonesia")

    cl = Client()
    cl.login("infogempaid", "passwordAnda")
    media_path = "GEMPATERBARU.png"
    cl.photo_upload(media_path, caption)
    print("Post berhasil diunggah ke Instagram.")


# Eksekusi proses utama
def main_process():
    try:
        # Ambil data dari API
        data = fetch_data_from_api()
        
        # Sinkronisasi ke CRUD
        sync_data_to_crud(data)
        
        # Lakukan proses berikutnya
        create_map()
        create_UI()
        up_to_instagram()

    except Exception as e:
        print(f"Error occurred: {e}")


# Jalankan
main_process()
