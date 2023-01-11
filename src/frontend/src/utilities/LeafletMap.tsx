import React from "react";
import { TileLayer, Polygon, Circle, MapContainer, Marker, Popup } from 'react-leaflet';

const LeafletMap = () => {
    const position: any = [51.505, -0.09]
    return (
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', border: '4px solid red', height: 500 }}>
            <MapContainer attributionControl={false} center={position} zoom={13} scrollWheelZoom={false} >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />
                <Marker position={position}>
                    <Popup>
                        A pretty CSS3 popup. <br /> Easily customizable.
                    </Popup>
                </Marker>
            </MapContainer>
        </div>
    )
}

export default LeafletMap;