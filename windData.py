import requests
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
from shapely.geometry import Point
from io import StringIO
import time
from datetime import datetime

def get_wind_data(station_url):
    try:
        response = requests.get(station_url, timeout=10)
        response.raise_for_status()
        
        # Hantera olika CSV-format
        lines = response.text.split('\n')
        data_start = 0
        for i, line in enumerate(lines):
            if line.startswith('Datum') or line.startswith('date') or ';' in line:
                data_start = i
                break
        
        df = pd.read_csv(
            StringIO('\n'.join(lines[data_start:])),
            sep=';',
            names=['date', 'wind_speed', 'quality'],
            dtype={'date': str, 'wind_speed': str, 'quality': str},
            on_bad_lines='warn',
            low_memory=False
        )
        
        # Rensa data
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['wind_speed'] = pd.to_numeric(df['wind_speed'], errors='coerce')
        df = df.dropna(subset=['date', 'wind_speed'])
        
        if df.empty:
            return None
            
        return {
            'avg_speed': df['wind_speed'].mean(),
            'max_speed': df['wind_speed'].max(),
            'data_points': len(df),
            'first_date': df['date'].min(),
            'last_date': df['date'].max()
        }
    
    except Exception as e:
        print(f"Fel vid hämtning av {station_url}: {e}")
        return None

def get_all_stations():
    url = "https://opendata-download-metobs.smhi.se/api/version/1.0/parameter/4.atom"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml-xml')
        
        stations = []
        for entry in soup.find_all('entry'):
            try:
                # Extrahera stationens ID
                atom_link = entry.find('link', {'type': 'application/atom+xml'})
                if not atom_link:
                    continue
                    
                href = atom_link.get('href', '')
                station_id = href.split('/')[-1].replace('.atom', '')
                
                # Extrahera position
                summary = entry.find('summary')
                if not summary:
                    continue
                    
                summary_text = summary.get_text()
                try:
                    lat = float(summary_text.split('Latitud: ')[1].split(' ')[0])
                    lon = float(summary_text.split('Longitud: ')[1].split(' ')[0])
                    height = float(summary_text.split('Höjd: ')[1].split(' ')[0])
                except (IndexError, ValueError):
                    continue
                
                # Hantera datum korrekt
                updated = entry.updated.text if entry.updated else ''
                try:
                    updated_dt = pd.to_datetime(updated, utc=True)
                except:
                    updated_dt = pd.NaT
                
                stations.append({
                    'station_id': station_id,
                    'name': entry.title.text.replace('Vindhastighet - ', ''),
                    'lat': lat,
                    'lon': lon,
                    'height': height,
                    'updated': updated_dt,
                    'data_url': f"https://opendata-download-metobs.smhi.se/api/version/latest/parameter/4/station/{station_id}/period/corrected-archive/data.csv"
                })
            except Exception as e:
                print(f"Fel vid parsing av station: {e}")
                continue
                
        return pd.DataFrame(stations)
    
    except Exception as e:
        print(f"Fel vid hämtning av stationer: {e}")
        return pd.DataFrame()

def process_all_stations():
    print("Hämtar stationer...")
    stations_df = get_all_stations()
    
    if stations_df.empty:
        print("Inga stationer kunde hämtas")
        return pd.DataFrame()
    
    print(f"Hittade {len(stations_df)} stationer")
    
    # Konvertera till datetime med UTC
    cutoff_date = pd.to_datetime('2020-01-01', utc=True)
    
    # Filtrera bort stationer utan giltigt datum
    valid_stations = stations_df[stations_df['updated'].notna()]
    
    if valid_stations.empty:
        print("Inga stationer med giltigt uppdateringsdatum")
        return pd.DataFrame()
    
    # Jämför datum i samma tidszon
    active_stations = valid_stations[valid_stations['updated'] > cutoff_date]
    
    if active_stations.empty:
        print("Inga aktiva stationer hittades efter 2020-01-01")
        return pd.DataFrame()
    
    print(f"Bearbetar {len(active_stations)} aktiva stationer...")
    
    wind_stats = []
    for idx, row in active_stations.iterrows():
        print(f"\nStation: {row['name']} (ID: {row['station_id']})")
        print(f"Uppdaterad: {row['updated']}")
        print(f"Position: {row['lat']:.4f}, {row['lon']:.4f}")
        
        stats = get_wind_data(row['data_url'])
        if stats:
            stats.update({
                'station_id': row['station_id'],
                'name': row['name'],
                'lat': row['lat'],
                'lon': row['lon'],
                'height': row['height'],
                'last_updated': row['updated']
            })
            wind_stats.append(stats)
            print(f"Lyckades hämta {stats['data_points']} datapunkter")
        else:
            print("Misslyckades att hämta data")
        
        time.sleep(0.5)  # Mildare fördröjning
    
    return pd.DataFrame(wind_stats)

# Resten av funktionerna förblir oförändrade

if __name__ == "__main__":
    start_time = time.time()
    import pandas as pd
    print("Startar hämtning av vinddata...")
    wind_data = pd.read_csv('svenska_vindstationer.csv') #process_all_stations()
    
    if not wind_data.empty:
        # Konvertera datum till strängar för CSV
        wind_data['last_updated'] = wind_data['last_updated'].dt.strftime('%Y-%m-%d %H:%M:%S')
        wind_data['first_date'] = wind_data['first_date'].dt.strftime('%Y-%m-%d')
        wind_data['last_date'] = wind_data['last_date'].dt.strftime('%Y-%m-%d')
        
        wind_data.to_csv('svenska_vindstationer.csv', index=False)
        print(f"\nData sparad till 'svenska_vindstationer.csv' (totalt {len(wind_data)} stationer)")
        
        print("\nSammanfattning:")
        print(f"Genomsnittlig vindhastighet: {wind_data['avg_speed'].mean():.1f} m/s")
        print(f"Högsta uppmätta vindhastighet: {wind_data['max_speed'].max():.1f} m/s")
        print(f"Tidigaste mätning: {wind_data['first_date'].min()}")
        print(f"Senaste mätning: {wind_data['last_date'].max()}")
        
        
    else:
        print("\nIngen vinddata kunde hämtas")
    
    print(f"\nKörningstid: {time.time() - start_time:.1f} sekunder")
