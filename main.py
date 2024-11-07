import time
import pandas as pd
import requests
from sqlalchemy import create_engine
import os

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
    else:
        print("Data sudah up-to-date. Tidak ada data baru.")

# Path ke file CSV relatif ke root repositori
csv_path = os.path.join("InfoGempaID_CSV", "DatasetGempa.csv")

def create_map():
    import matplotlib.pyplot as plt
    import sqlite3
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    
    # Fungsi untuk konversi lintang dan bujur dari format teks ke float
    def convert_coordinates(lintang, bujur):
        # Konversi lintang
        if 'LS' in lintang:
            latitude = -float(lintang.replace('LS', '').strip())
        elif 'LU' in lintang:
            latitude = float(lintang.replace('LU', '').strip())
        else:
            raise ValueError("Format lintang tidak dikenal. Harus ada 'LS' atau 'LU'.")
    
        # Konversi bujur
        if 'BT' in bujur:
            longitude = float(bujur.replace('BT', '').strip())
        elif 'BB' in bujur:
            longitude = -float(bujur.replace('BB', '').strip())
        else:
            raise ValueError("Format bujur tidak dikenal. Harus ada 'BT' atau 'BB'.")
        
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
    
    # Path ke database
    csv_path = os.path.join("InfoGempaID_CSV", "DatasetGempa.csv")
    
    # Membaca data terbaru dari database
    data = read_data_from_csv(csv_path)
    
    # Mengonversi lintang dan bujur
    latitude, longitude = convert_coordinates(data['lintang'], data['bujur'])
    
    # Membuat plot dengan cartopy
    fig = plt.figure(figsize=(9, 18))
    ax = plt.axes(projection=ccrs.PlateCarree())
    
    # Menambahkan peta dasar dan fitur
    ax.set_extent([94, 141, -15, 12], crs=ccrs.PlateCarree())  # Batas peta untuk wilayah Indonesia
    ax.add_feature(cfeature.LAND, color='lightgray')
    ax.add_feature(cfeature.OCEAN, color='#25656a')
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    
    # Plot lokasi gempa
    ax.plot(longitude, latitude, 'ro', markersize=4, transform=ccrs.PlateCarree(), label="Lokasi Gempa")
    
    # Menambahkan efek gelombang di sekitar titik lokasi gempa
    num_rings = 10  # Jumlah gelombang
    ring_spacing = 0.7  # Jarak antara lingkaran dalam derajat
    for i in range(1, num_rings + 1):
        circle_radius = i * ring_spacing  # Radius lingkaran dalam derajat
        circle = plt.Circle((longitude, latitude), circle_radius, color='red', fill=False, linestyle='--', transform=ccrs.PlateCarree())
        ax.add_patch(circle)
    
    # Sembunyikan grid dan axis
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['bottom'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    
    # Simpan plot ke dalam file
    plt.savefig(r'D:\Coding\InfoGempaID\lokasi_baru1.png', bbox_inches='tight', pad_inches=0)
    
    # Menampilkan plot
    plt.show()


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
    import sqlite3

    def read_data_from_csv(csv_path):
        # Membaca data dari file CSV
        df = pd.read_csv(csv_path)
        
        # Mengambil data terbaru berdasarkan kolom DateTime
        latest_data = df.sort_values('DateTime', ascending=False).iloc[0]
        
        # Jika data ditemukan, kembalikan dalam bentuk dictionary
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


    capt = (f"🌍 Gempa Terkini ! 🌍\n\n📍  Lokasi     : {data['wilayah']}\n📅 Tanggal    : {data['tanggal']}\n🕒 Waktu      : {data['waktu']}\n"
            f"🌐 Koordinat  : {data['bujur']} LS, {data['lintang']} BT\n💥 Magnitude  : {data['magnitude']}\n"
            f"🌊 Potensi Tsunami: {data['potensi']}\n🔻 Kedalaman  : {data['kedalaman']}\n\n"
            f"Kami mengimbau untuk tetap waspada dan mengikuti informasi resmi dari pihak berwenang. "
            f"Jaga keselamatan diri dan keluarga! 🙏\n#Gempa #Kesiapsiagaan #Indonesia #InfoIDGempa #gempa #earthquake")


    image_path = os.path.join("InfoGempaID_CSV", "GEMPATERBARU.png")

    # Login dan upload menggunakan instagrapi
    cl = Client()
    cl.login("infogempaid", "Megamode12")

    # Upload gambar yang telah diubah ukurannya
    media = cl.photo_upload(path=image_path, caption=capt)

fetch_and_update_data(csv_path)
