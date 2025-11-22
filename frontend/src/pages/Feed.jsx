import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MapPin, Users, Star, ArrowRight, Smartphone, LayoutGrid } from 'lucide-react';
import TikTokFeed from '../components/TikTokFeed';

export default function Feed() {
    const [users, setUsers] = useState([]);
    const [selectedUserId, setSelectedUserId] = useState(null);
    const [feed, setFeed] = useState([]);
    const [loading, setLoading] = useState(false);
    const [viewMode, setViewMode] = useState('tiktok'); // 'tiktok' or 'grid'

    // Fetch users for selector
    useEffect(() => {
        const fetchUsers = async () => {
            const res = await axios.get('http://localhost:8000/debug/map-data');
            setUsers(res.data.users);
            if (res.data.users.length > 0 && !selectedUserId) {
                setSelectedUserId(res.data.users[0].id);
            }
        };
        fetchUsers();
    }, []);

    // Fetch Feed
    useEffect(() => {
        if (!selectedUserId) return;
        const fetchFeed = async () => {
            setLoading(true);
            try {
                // Mock location for now (NYC Center)
                const res = await axios.get(`http://localhost:8000/feed?user_id=${selectedUserId}&lat=40.7128&lon=-74.0060`);
                setFeed(res.data.feed);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        fetchFeed();
    }, [selectedUserId]);

    const handleSave = async (venueId) => {
        try {
            await axios.post('http://localhost:8000/ingest/interaction', {
                user_id: selectedUserId,
                venue_id: venueId,
                interaction_type: 'saved',
                duration: 0
            });
            alert("Saved!");
        } catch (e) {
            alert("Failed to save");
        }
    };

    // TikTok mode - full screen
    if (viewMode === 'tiktok' && selectedUserId) {
        return (
            <div className="h-full relative">
                {/* User Selector Overlay */}
                <div className="absolute top-4 left-4 right-4 z-50 flex justify-between items-center">
                    <select
                        className="bg-black/50 backdrop-blur text-white border border-white/20 rounded-lg px-4 py-2 outline-none text-sm"
                        value={selectedUserId || ''}
                        onChange={e => setSelectedUserId(e.target.value)}
                    >
                        {users.map(u => (
                            <option key={u.id} value={u.id}>{u.name}</option>
                        ))}
                    </select>

                    <button
                        onClick={() => setViewMode('grid')}
                        className="bg-black/50 backdrop-blur text-white border border-white/20 rounded-lg px-4 py-2 flex items-center gap-2 text-sm hover:bg-black/70 transition"
                    >
                        <LayoutGrid className="w-4 h-4" />
                        Grid View
                    </button>
                </div>

                <TikTokFeed userId={selectedUserId} />
            </div>
        );
    }

    // Grid mode - traditional view
    return (
        <div className="h-full flex flex-col bg-gray-100">
            {/* Header / Selector */}
            <div className="bg-white border-b border-gray-200 p-6 flex justify-between items-center shadow-sm z-10">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Your Feed</h1>
                    <p className="text-gray-500 text-sm">Personalized recommendations based on your circle.</p>
                </div>
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => setViewMode('tiktok')}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                    >
                        <Smartphone className="w-4 h-4" />
                        TikTok View
                    </button>
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-600">Viewing as:</span>
                        <select
                            className="border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-indigo-500 bg-gray-50"
                            value={selectedUserId || ''}
                            onChange={e => setSelectedUserId(e.target.value)}
                        >
                            {users.map(u => (
                                <option key={u.id} value={u.id}>{u.name}</option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Feed Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-3xl mx-auto space-y-6">
                    {loading ? (
                        <div className="text-center py-12 text-gray-500">Curating your feed...</div>
                    ) : feed.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">No recommendations yet. Add friends or interests!</div>
                    ) : (
                        feed.map((item) => (
                            <div key={item.venue_id} className="bg-white rounded-2xl shadow-sm overflow-hidden hover:shadow-md transition-shadow border border-gray-100">
                                <div className="flex">
                                    {/* Left: Image Placeholder */}
                                    <div className="w-1/3 bg-gray-200 min-h-[200px] relative">
                                        <img
                                            src={`https://source.unsplash.com/random/400x400/?${item.payload?.category || 'restaurant'}`}
                                            alt={item.name}
                                            className="w-full h-full object-cover opacity-90"
                                            onError={(e) => e.target.style.display = 'none'}
                                        />
                                        <div className="absolute top-4 left-4 bg-white/90 backdrop-blur px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide text-gray-800">
                                            {item.payload?.category}
                                        </div>
                                    </div>

                                    {/* Right: Content */}
                                    <div className="w-2/3 p-6 flex flex-col justify-between">
                                        <div>
                                            <div className="flex justify-between items-start mb-2">
                                                <h2 className="text-xl font-bold text-gray-900">{item.name}</h2>
                                                <div className="flex items-center gap-1 text-yellow-500 font-bold">
                                                    <Star className="w-4 h-4 fill-current" />
                                                    {/* Show actual match score normalized to 5 stars roughly */}
                                                    {Math.min(5.0, Math.max(1.0, Math.round(item.match_score * 5 * 10) / 10))}
                                                </div>
                                            </div>
                                            <p className="text-gray-600 text-sm line-clamp-2 mb-4">{item.description}</p>

                                            {/* "Why" Badges */}
                                            <div className="flex flex-wrap gap-2 mb-4">
                                                {item.friend_activity && (
                                                    <div className="flex items-center gap-2 px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg text-sm font-medium">
                                                        <Users className="w-4 h-4" />
                                                        {item.friend_activity}
                                                    </div>
                                                )}
                                                {/* Only show Nearby if we actually calculated it (omitted for now as we mock location) */}
                                            </div>
                                        </div>

                                        <div className="flex gap-3 mt-4">
                                            <button className="flex-1 bg-black text-white py-2.5 rounded-xl font-bold text-sm hover:bg-gray-800 transition-colors flex items-center justify-center gap-2">
                                                Book Table <ArrowRight className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleSave(item.venue_id)}
                                                className="px-4 py-2.5 border border-gray-200 rounded-xl font-bold text-sm hover:bg-gray-50 text-gray-600"
                                            >
                                                Save
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    )
}
