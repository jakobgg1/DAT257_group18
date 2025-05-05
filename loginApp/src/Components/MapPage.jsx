import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { useEffect } from 'react';

// 🔧 Fix Leaflet marker icon issues in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

function MapPage() {
    return (
        <div className="map-page">
            {/* Nav */}
            <nav className="navbar">
                <a href="/" className="logo">OptiSolar</a>
                <div className="nav-links">
                    <a href="/">Home</a>
                    <a href="/map">Map</a>
                    <a href="/about">About</a>
                </div>
            </nav>

            {/* Title */}
            <div className="container">
                <h1 className="page-title">Sweden Solar Map</h1>

                {/* Map */}
                <MapContainer
                    center={[62.0, 15.0]}
                    zoom={5}
                    scrollWheelZoom={false}
                    style={{ height: '500px', width: '100%', borderRadius: '8px', boxShadow: '0 2px 5px rgba(0,0,0,0.05)' }}
                >
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution="&copy; OpenStreetMap contributors"
                    />
                    <Marker position={[59.3293, 18.0686]}>
                        <Popup>Stockholm</Popup>
                    </Marker>
                </MapContainer>
            </div>

            {/* Footer */}
            <footer className="footer">
                <p>&copy; 2025 OptiSolar. All rights reserved.</p>
            </footer>
        </div>
    );
}

export default MapPage;
