import React, { useEffect, useState } from 'react';
import axios from 'axios';

export default function FeedView({ userId }) {
    const [feed, setFeed] = useState([]);
    const [loading, setLoading] = useState(false);
    const [bookingStatus, setBookingStatus] = useState(null);

    useEffect(() => {
        if (!userId) return;

        const fetchFeed = async () => {
            setLoading(true);
            try {
                // Mock location for now
                const response = await axios.get(`http://localhost:8000/feed?user_id=${userId}&lat=40.7128&lon=-74.0060`);
                setFeed(response.data.feed);
            } catch (error) {
                console.error("Error fetching feed:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchFeed();
    }, [userId]);

    const handleBook = async (venueId) => {
        setBookingStatus({ type: 'info', msg: 'Booking...' });
        try {
            const response = await axios.post('http://localhost:8000/agent/action', {
                user_id: userId,
                venue_id: venueId,
                party_size: 2,
                time: "20:00" // Default time
            });
            setBookingStatus({ type: 'success', msg: response.data.message });
        } catch (error) {
            setBookingStatus({ type: 'error', msg: 'Booking failed' });
        }
    };

    if (!userId) {
        return <div className="p-4 text-gray-500">Select a user on the map to view their feed.</div>;
    }

    return (
        <div className="h-full overflow-y-auto p-4 bg-gray-50">
            <h2 className="text-xl font-bold mb-4">Recommendation Feed</h2>
            <p className="text-sm text-gray-600 mb-4">User ID: {userId}</p>

            {bookingStatus && (
                <div className={`p-2 mb-4 rounded ${bookingStatus.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'}`}>
                    {bookingStatus.msg}
                </div>
            )}

            {loading ? (
                <div>Loading...</div>
            ) : (
                <div className="space-y-4">
                    {feed.map(item => (
                        <div key={item.venue_id} className="bg-white p-4 rounded shadow border border-gray-200">
                            <div className="flex justify-between items-start">
                                <h3 className="font-bold text-lg">{item.name}</h3>
                                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                                    {Math.round(item.match_score * 100)}% Match
                                </span>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{item.description}</p>

                            {item.friend_activity && (
                                <div className="mt-2 text-sm text-purple-600 font-medium">
                                    👥 {item.friend_activity}
                                </div>
                            )}

                            <div className="mt-3 flex justify-between items-center text-xs text-gray-500">
                                <span>Vibe: {item.vibe_match}</span>
                                <span>Social: {item.social_score}</span>
                            </div>

                            <button
                                onClick={() => handleBook(item.venue_id)}
                                className="mt-3 w-full bg-black text-white py-2 rounded hover:bg-gray-800 transition"
                            >
                                Book Table
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
