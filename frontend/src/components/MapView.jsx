import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import axios from 'axios';
import L from 'leaflet';

// Fix Leaflet marker icons
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const NYC_CENTER = [40.7128, -74.0060];

export default function MapView({ venues, users, selectedUserId, onSelectUser, onRefresh }) {
    // Data is now passed in via props to share state with UserList

    const handleInteraction = async (venueId, type) => {
        if (!selectedUserId) {
            alert("Please select a user first!");
            return;
        }
        try {
            await axios.post('http://localhost:8000/ingest/interaction', {
                user_id: selectedUserId,
                venue_id: venueId,
                interaction_type: type,
                duration: 60
            });
            alert(`Marked as ${type}!`);
            onRefresh(); // Refresh to update feed/map
        } catch (e) {
            console.error(e);
            alert("Failed to record interaction");
        }
    };

    return (
        <div className="h-full w-full">
            <MapContainer center={NYC_CENTER} zoom={13} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />

                {venues.map(venue => (
                    <Marker key={venue.venue_id} position={[venue.location.lat, venue.location.lon]}>
                        <Popup>
                            <div className="p-2 min-w-[200px]">
                                <h3 className="font-bold text-lg">{venue.name}</h3>
                                <p className="text-sm text-gray-600 mb-2">{venue.category}</p>
                                <p className="text-xs text-gray-500 mb-3">{venue.description}</p>

                                {selectedUserId ? (
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleInteraction(venue.venue_id, 'going')}
                                            className="flex-1 bg-black text-white py-1 rounded text-xs hover:bg-gray-800"
                                        >
                                            I'm Going
                                        </button>
                                        <button
                                            onClick={() => handleInteraction(venue.venue_id, 'saved')}
                                            className="flex-1 border border-gray-300 py-1 rounded text-xs hover:bg-gray-50"
                                        >
                                            Save
                                        </button>
                                    </div>
                                ) : (
                                    <div className="text-xs text-red-500 italic">
                                        Select a user to interact
                                    </div>
                                )}
                            </div>
                        </Popup>
                    </Marker>
                ))}

                {users.map(user => (
                    <Circle
                        key={user.id}
                        center={[40.7128 + (Math.random() - 0.5) * 0.05, -74.0060 + (Math.random() - 0.5) * 0.05]} // Mock user location
                        radius={selectedUserId === user.id ? 150 : 100}
                        pathOptions={{
                            color: selectedUserId === user.id ? 'red' : 'blue',
                            fillColor: selectedUserId === user.id ? 'red' : 'blue'
                        }}
                        eventHandlers={{
                            click: () => onSelectUser(user.id)
                        }}
                    >
                        <Popup>
                            <div className="p-2">
                                <h3 className="font-bold">{user.name}</h3>
                                <button
                                    className="mt-2 bg-blue-500 text-white px-2 py-1 rounded text-xs"
                                    onClick={() => onSelectUser(user.id)}
                                >
                                    Select User
                                </button>
                            </div>
                        </Popup>
                    </Circle>
                ))}
            </MapContainer>
        </div>
    );
}
