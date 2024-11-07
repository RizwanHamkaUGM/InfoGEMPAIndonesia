import time
import pandas as pd
import requests
import os
import subprocess
from sqlalchemy import create_engine

# Fungsi untuk mengambil dan memperbarui data dari BMKG
def fetch_and_update_data(csv_path):
    url = 'https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json'
    response = requests.get(url)
    response_data = response.json()
    
    # Normalisasi JSON menjadi DataFrame
    df = pd.json_normalize(response_data['Infogempa']['gempa'])
    
    # Pilih kolom yang relevan
    df_relevant = df[['Tanggal', 'Jam', 'Coordinates', 'DateTime', 'Lintang', 'Bujur', 'Magnitude', 'Kedalaman', 'Wilayah', 'Potensi', 'Dirasakan', 'Shakemap']]
    
    # Cek apakah file CSV sudah ada
    if os.path.exists(csv_path):
        # Jika file sudah ada, baca data yang ada dan cari data terbaru
        existing_data = pd.read_csv(csv_path)
        latest_date_in_file = existing_data['DateTime'].max()
        
        # Filter data hanya yang terbaru
        df_relevant = df_relevant[df_relevant['DateTime'] > latest_date_in_file]
    else:
        # Jika file CSV belum ada, buat file baru dengan header dan data pertama
        df_relevant.to_csv(csv_path, index=False)
        print(f"File CSV baru dibuat di {csv_path}")
    
    # Tambahkan data baru ke CSV jika ada
    if not df_relevant.empty:
        df_relevant.to_csv(csv_path, mode='a', index=False, header=False)
        print("Data terbaru ditambahkan ke CSV.")
        
        # Jika ada data baru, jalankan proses berikut
        create_map()
        time.sleep(5)
        create_UI()
        time.sleep(5)
        up_to_instagram()
        
        # Komit dan push perubahan ke GitHub
        commit_and_push_to_github()
    else:
        print("Data sudah up-to-date. Tidak ada data baru.")

# Path ke file CSV relatif ke root repositori
csv_path = os.path.join("InfoGempaID_CSV", "DatasetGempa.csv")

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

    def read_data_from_csv(csv_path):
        df = pd.read_csv(csv_path)
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

    # Membaca data terbaru dari CSV
    data = read_data_from_csv(csv_path)
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

    def read_data_from_csv(csv_path):
        df = pd.read_csv(csv_path)
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

    data = read_data_from_csv(csv_path)
    template_path = os.path.join("InfoGempaID_CSV", "UiGempaTanpaMap.png")
    output_path = os.path.join("InfoGempaID_CSV", "GEMPATERBARU.png")
    map_path = os.path.join("InfoGempaID_CSV", "lokasi_baru1.png")

    if data:
        create_earthquake_image(data, template_path, output_path, map_path)

def up_to_instagram():
    from instagrapi import Client

    def read_data_from_csv(csv_path):
        df = pd.read_csv(csv_path)
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

    data = read_data_from_csv(csv_path)

    capt = (f"🌍 Gempa Terkini ! 🌍\n\n📍  Lokasi     : {data['wilayah']}\n📅  Tanggal   : {data['tanggal']}\n"
            f"🕗  Waktu     : {data['waktu']}\n🎯  Koordinat : {data['koordinat']}\n"
            f"📊  Magnitudo : {data['magnitude']} SR\n📏  Kedalaman : {data['kedalaman']}\n"
            f"📢  Potensi   : {data['potensi']}\n\nData resmi dari BMKG.")

    cl = Client()
    cl.login("infogempaid", "Megamode12")
    media_path = os.path.join("InfoGempaID_CSV", "GEMPATERBARU.png")
    cl.photo_upload(media_path, capt)
    print("Post berhasil diunggah ke Instagram.")

def commit_and_push_to_github():
    try:
        commit_message = "Update earthquake map and data"
        subprocess.run(["git", "add", "InfoGempaID_CSV/lokasi_baru1.png"], check=True)
        subprocess.run(["git", "add", "InfoGempaID_CSV/GEMPATERBARU.png"], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Perubahan berhasil dikomit dan dipush ke GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"Terjadi kesalahan saat mencoba mengkomit/push: {e}")

# Eksekusi proses utama
fetch_and_update_data(csv_path)
