from geopy.geocoders import Nominatim
from shapely.geometry import Point
from concurrent.futures import ThreadPoolExecutor
from tenacity import retry, wait_exponential, stop_after_attempt
import threading
import geopandas as gpd 
import requests
import csv 
import time
import json
import os
import numpy as np

# This script queries solar irradiation data (global, direct, diffuse) for a grid over Sweden.
# It returns results as a CSV file containing coordinates, place names, average values, and clarity ratio.

# Load or initialize location cache for faster runtime.
cache_file = "location_cache.json"
if os.path.exists(cache_file):
    with open(cache_file, "r", encoding="utf-8") as f:
        location_cache = json.load(f)
else:
    location_cache = {}

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(5))

#Fetches irradition data (global, direct, diffuse) from SHMI's STRÅNG API 
#Returns a list of avg values for given coordinate and date range
def get_irradiation (lat, lon, data_type, date_from, date_to):

    vaild_data_types= { #check that data_type is vaild. 
        "global" : 117,
        "direct" : 120,
        "diffuse" : 119
    }
    
    if data_type not in vaild_data_types:
        return [] 
    
    data_type_code = vaild_data_types[data_type]

    url = ((
        f"https://opendata-download-metanalys.smhi.se/api/category/strang1g/version/1/"
        f"geotype/point/lon/{lon:.2f}/lat/{lat:.2f}/parameter/{data_type_code}/data.txt?"
        f"from={date_from}&to={date_to}&interval=daily")
    )

    response = requests.get(url, timeout=10)  
    response.raise_for_status()

    raw_data = response.text.splitlines()
    irradiation_values = []

    for line in raw_data:
        if "-999" not in line:
            parts = line.strip().split()
            if len(parts) == 5:
                date = parts[1]
                value = float(parts[-1])
                if value >= 0:
                    irradiation_values.append((date, value))

    return irradiation_values


# Uses reverse goecoding to get place name from coordinates
def get_location_name(lat,lon):
    key = (round(lat,2), round(lon,2))
    if key in location_cache:
        return location_cache[key]

    geolocator = Nominatim(user_agent="solar_mapper")
    try: 
        location = geolocator.reverse((lat,lon), exactly_one=True, timeout=10)
        time.sleep(1) #API limit 1s
        address = location.raw.get("address", {})

        location_name = (
            address.get("town") or 
            address.get("city") or 
            address.get("municipality") or 
            address.get("village") or 
            address.get("county") or
            "Unknown"
        )

        location_cache[key] = location_name   

        # Save updated cache immediately
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(location_cache, f, ensure_ascii=False, indent=2)

        return location_name

    except:
        return "Unknown"

# Main function to iterate over a grid across Sweden aand collects irraditation data
# resolution_deg defines how fine-grained the grid is (e.g. which zoom-level on the map you are)
def collect_data_for_sweden(date_from, date_to, resolution_deg_lat,resolution_deg_lon):
    lat_range = np.arange(55.0, 69.1, resolution_deg_lat)
    lon_range = np.arange(11.0, 25.1, resolution_deg_lon)

    world = gpd.read_file("data/ne_110m_admin_0_countries.shp")
    sweden = world[world["ADMIN"] == "Sweden"]

    with open("soldata_svergieV2.csv", "w", newline="") as file: 
        writer = csv.writer(file)
        writer.writerow(["location", "lat", "lon", "global_avg", "direct_avg", "diffuse_avg", "clarity_ratio"])
        with ThreadPoolExecutor(max_workers=10) as executor:
            for lat in lat_range:
                for lon in lon_range:

                    location_point = Point(lon,lat)

                    if not location_point.within(sweden.geometry.iloc[0]):
                        print(f"Skipped | {location_point}")
                        continue
                    
                    # Fetch all three types of irradiation data
                    multithread_global_values = executor.submit(get_irradiation, lat, lon, "global", date_from, date_to)
                    multithread_direct_values = executor.submit(get_irradiation, lat, lon, "direct", date_from, date_to)
                    multithread_diffuse_values = executor.submit(get_irradiation, lat, lon, "diffuse", date_from, date_to)
                    try: 
                        global_values = dict(multithread_global_values.result())
                        direct_values = dict(multithread_direct_values.result())
                        diffuse_values = dict(multithread_diffuse_values.result())
                    except Exception as e:
                        print(f"API call failed for ({lat:.2f},{lon:.2f}): {e}")
                        continue

                    common_dates = set(global_values.keys()) & set(direct_values.keys()) & set(diffuse_values.keys())

                    # Proceed if data is complete and valid
                    if common_dates:
                        global_avg = sum(global_values[d] for d in common_dates) / len(common_dates)
                        direct_avg = sum(direct_values[d] for d in common_dates) / len(common_dates)
                        diffuse_avg = sum(diffuse_values[d] for d in common_dates) / len(common_dates)
                        clarity = direct_avg / global_avg if global_avg else 0

                        # Write data to CSV file
                        #location_name = get_location_name(lat,lon)
                        writer.writerow([
                            round(lat,2),
                            round(lon,2),
                            round(global_avg, 2),
                            round(direct_avg, 2),
                            round(diffuse_avg, 2),
                            round(clarity, 2)
                        ])

                    # Print out
                    print(f"{lat:.2f}, {lon:.2f} - Global: {global_avg:.1f}, Direct: {direct_avg}, Diffuse: {diffuse_avg}, Clarity: {clarity:.2f}")
                else:   

                    print(f"Skipped ({lat:.2f}, {lon:.2f}) - Incomplete data")


if __name__ == "__main__":
    collect_data_for_sweden(20200101,20250426, resolution_deg_lat=0.0225,resolution_deg_lon=0.0417)

