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
                                    {/* Left: Gradient Background */}
                                    <div className="w-1/3 min-h-[200px] relative" style={{
                                        background: item.categories?.[0] === 'cafe' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' :
                                                   item.categories?.[0] === 'bar' ? 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' :
                                                   item.categories?.[0] === 'gallery' ? 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' :
                                                   item.categories?.[0] === 'bakery' ? 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' :
                                                   'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)'
                                    }}>
                                        <div className="absolute inset-0 flex items-center justify-center text-white">
                                            <div className="text-6xl opacity-20">
                                                {item.categories?.[0] === 'cafe' && '☕'}
                                                {item.categories?.[0] === 'bar' && '🍸'}
                                                {item.categories?.[0] === 'gallery' && '🎨'}
                                                {item.categories?.[0] === 'bakery' && '🥐'}
                                                {item.categories?.[0] === 'restaurant' && '🍽️'}
                                            </div>
                                        </div>
                                        <div className="absolute bottom-4 left-4">
                                            {item.categories?.slice(0, 2).map((cat, idx) => (
                                                <span key={idx} className="inline-block px-2 py-1 bg-white/20 backdrop-blur text-white text-xs rounded mr-1">
                                                    {cat}
                                                </span>
                                            ))}
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

                                            {/* Algorithm Transparency - Score Breakdown */}
                                            {item.explanation && (
                                                <div className="mb-4">
                                                    {/* Final Score */}
                                                    <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-3 rounded-lg mb-3">
                                                        <div className="flex justify-between items-center mb-2">
                                                            <div>
                                                                <div className="text-xs opacity-90">Match Score</div>
                                                                <div className="text-2xl font-bold">{Math.round(item.final_score * 100)}%</div>
                                                            </div>
                                                            <div className="text-right">
                                                                <div className="text-xs opacity-75 max-w-[200px]">
                                                                    0.3×Taste + 0.4×Social + 0.2×Proximity + 0.1×Trending
                                                                </div>
                                                            </div>
                                                        </div>
                                                        <div className="text-[10px] bg-white/20 rounded px-2 py-1">
                                                            ⏱️ Social score: Only 10s+ watch times count
                                                        </div>
                                                    </div>

                                                    <div className="space-y-2">
                                                        {/* Taste Match */}
                                                        <div className="text-xs">
                                                            <div className="flex justify-between mb-1">
                                                                <span className="text-gray-700 font-medium">Taste Match (30%)</span>
                                                                <span className="font-bold text-blue-600">{Math.round(item.explanation.taste_match.score * 100)}%</span>
                                                            </div>
                                                            <div className="w-full h-1.5 bg-gray-200 rounded-full">
                                                                <div className="h-full bg-blue-500 rounded-full" style={{ width: `${item.explanation.taste_match.score * 100}%` }} />
                                                            </div>
                                                        </div>

                                                        {/* Social Proof with Friend Details */}
                                                        <div className="text-xs">
                                                            <div className="flex justify-between mb-1">
                                                                <span className="text-gray-700 font-medium">Friend Activity (40%)</span>
                                                                <span className="font-bold text-indigo-600">{Math.round(item.explanation.social_proof.score * 100)}%</span>
                                                            </div>
                                                            <div className="w-full h-1.5 bg-gray-200 rounded-full mb-2">
                                                                <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${item.explanation.social_proof.score * 100}%` }} />
                                                            </div>
                                                            {item.explanation.social_proof.contributors.length > 0 && (
                                                                <div className="space-y-1 pl-2">
                                                                    {item.explanation.social_proof.contributors.slice(0, 3).map((c, idx) => (
                                                                        <div key={idx} className="flex justify-between items-center bg-indigo-50 p-1.5 rounded">
                                                                            <span className="text-gray-700">
                                                                                {c.friend ? (
                                                                                    <>
                                                                                        {c.friend}{' '}
                                                                                        {c.action === 'shared' && '📤'}
                                                                                        {c.action === 'saved' && '💾'}
                                                                                        {c.action === 'viewed' && '👀'}
                                                                                    </>
                                                                                ) : (
                                                                                    `${c.mutuals} mutuals`
                                                                                )}
                                                                            </span>
                                                                            <span className="text-green-600 font-bold text-[10px]">+{c.boost}</span>
                                                                        </div>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>

                                                        {/* Proximity */}
                                                        <div className="text-xs">
                                                            <div className="flex justify-between mb-1">
                                                                <span className="text-gray-700 font-medium">Proximity (20%)</span>
                                                                <span className="font-bold text-green-600">{Math.round(item.explanation.proximity.score * 100)}%</span>
                                                            </div>
                                                            <div className="w-full h-1.5 bg-gray-200 rounded-full">
                                                                <div className="h-full bg-green-500 rounded-full" style={{ width: `${item.explanation.proximity.score * 100}%` }} />
                                                            </div>
                                                        </div>

                                                        {/* Trending */}
                                                        <div className="text-xs">
                                                            <div className="flex justify-between mb-1">
                                                                <span className="text-gray-700 font-medium">Trending (10%)</span>
                                                                <span className="font-bold text-orange-600">{Math.round(item.explanation.trending.score * 100)}%</span>
                                                            </div>
                                                            <div className="w-full h-1.5 bg-gray-200 rounded-full">
                                                                <div className="h-full bg-orange-500 rounded-full" style={{ width: `${item.explanation.trending.score * 100}%` }} />
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
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
