import requests

def frange(start, stop, step):
    while start <= stop:
        yield round(start, 2)
        start += step

lat_vals = list(frange(55.0, 69.0, 1.0))
lon_vals = list(frange(11.0, 24.0, 1.0))

coordinates = [{"lat": lat, "lon": lon} for lat in lat_vals for lon in lon_vals]

batch_size = 50
date = "20240401T12"
parameter = "117"

for i in range(0, len(coordinates), batch_size):
    batch = coordinates[i:i+batch_size]
    lats = ",".join(str(coord["lat"]) for coord in batch)
    lons = ",".join(str(coord["lon"]) for coord in batch)

    url = (
        f"https://opendata-download-metanalys.smhi.se/api/category/strang1g/version/1/"
        f"geotype/multipoint/validtime/{date}/parameter/{parameter}/data.json"
        f"?lat={lats}&lon={lons}"
    )

    print(f"\n🔄 Hämtar batch {i}–{i+len(batch)-1}...")
    response = requests.get(url)

    try:
        data = response.json()

        # Om datan är en lista – direkt med punkter
        if isinstance(data, list):
            for point in data:
                print(f"✅ ({point['lat']}, {point['lon']}) => {point['value']} W/m²")

        # Om datan är ett objekt som innehåller 'value'
        elif isinstance(data, dict) and "value" in data:
            for point in data["value"]:
                print(f"✅ ({point['lat']}, {point['lon']}) => {point['value']} W/m²")

        else:
            print("⚠️ Oväntat format på svaret:", data)

    except ValueError:
        print("❌ Kunde inte tolka JSON. Här är svaret:")
        print(response.text)
    
