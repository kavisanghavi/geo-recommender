import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { User, MapPin, Users, Heart, Calendar, Clock, Bookmark, Share2, Eye } from 'lucide-react';

export default function UserProfile() {
    const [users, setUsers] = useState([]);
    const [selectedUserId, setSelectedUserId] = useState(null);
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(false);

    // Fetch all users for the selector
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

    // Fetch profile details when selected
    useEffect(() => {
        if (!selectedUserId) return;
        const fetchProfile = async () => {
            setLoading(true);
            try {
                const res = await axios.get(`http://localhost:8000/user/${selectedUserId}`);
                setProfile(res.data);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        fetchProfile();
    }, [selectedUserId]);

    if (!profile && !loading) return <div className="p-8">Loading...</div>;

    return (
        <div className="h-full flex flex-col bg-gray-50">
            {/* Header / Selector */}
            <div className="bg-white border-b border-gray-200 p-6 flex justify-between items-center">
                <h1 className="text-2xl font-bold">User Profiles</h1>
                <select
                    className="border border-gray-300 rounded-lg px-4 py-2 outline-none focus:ring-2 focus:ring-indigo-500"
                    value={selectedUserId || ''}
                    onChange={e => setSelectedUserId(e.target.value)}
                >
                    {users.map(u => (
                        <option key={u.id} value={u.id}>{u.name}</option>
                    ))}
                </select>
            </div>

            {loading ? (
                <div className="p-8 text-center text-gray-500">Loading profile...</div>
            ) : profile && (
                <div className="flex-1 overflow-y-auto p-8">
                    <div className="max-w-4xl mx-auto space-y-6">

                        {/* Stats Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-white p-6 rounded-2xl shadow-sm flex items-center gap-4">
                                <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600">
                                    <Users className="w-6 h-6" />
                                </div>
                                <div>
                                    <div className="text-2xl font-bold">{profile.friends?.length || 0}</div>
                                    <div className="text-sm text-gray-500">Friends</div>
                                </div>
                            </div>
                            <div className="bg-white p-6 rounded-2xl shadow-sm flex items-center gap-4">
                                <div className="w-12 h-12 bg-pink-100 rounded-full flex items-center justify-center text-pink-600">
                                    <Heart className="w-6 h-6" />
                                </div>
                                <div>
                                    <div className="text-2xl font-bold">{profile.interests?.length || 0}</div>
                                    <div className="text-sm text-gray-500">Interests</div>
                                </div>
                            </div>
                            <div className="bg-white p-6 rounded-2xl shadow-sm flex items-center gap-4">
                                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center text-green-600">
                                    <MapPin className="w-6 h-6" />
                                </div>
                                <div>
                                    <div className="text-2xl font-bold">{profile.interactions?.length || 0}</div>
                                    <div className="text-sm text-gray-500">Places</div>
                                </div>
                            </div>
                        </div>

                        {/* Interests */}
                        <div className="bg-white p-6 rounded-2xl shadow-sm">
                            <h3 className="font-bold text-lg mb-4">Interests</h3>
                            <div className="flex flex-wrap gap-2">
                                {(profile.user?.interests || profile.interests || []).map((tag, i) => (
                                    <span key={i} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Friends */}
                        <div className="bg-white p-6 rounded-2xl shadow-sm">
                            <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                                <Users className="w-5 h-5" />
                                Friends ({(profile.friends || []).length})
                            </h3>
                            <div className="grid grid-cols-2 gap-3">
                                {(profile.friends || []).map(f => (
                                    <div key={f.id} className="border border-gray-200 rounded-xl p-4 hover:border-indigo-300 transition">
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <h4 className="font-semibold text-gray-900">{f.name}</h4>
                                                <div className="flex flex-wrap gap-1 mt-2">
                                                    {f.interests?.slice(0, 3).map((interest, idx) => (
                                                        <span key={idx} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                                                            {interest}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                                {(profile.friends || []).length === 0 && <div className="col-span-2 text-center py-8 text-gray-400 italic">No friends yet</div>}
                            </div>
                        </div>

                        {/* My Places (Saved Venues) */}
                        <div className="bg-white p-6 rounded-2xl shadow-sm">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-bold text-lg flex items-center gap-2">
                                    <Bookmark className="w-5 h-5 text-blue-600" />
                                    My Places ({(profile.watch_history || []).filter(h => h.action === 'saved').length})
                                </h3>
                                <button
                                    onClick={() => window.location.reload()}
                                    className="text-sm text-indigo-600 hover:text-indigo-700 font-medium"
                                >
                                    🔄 Refresh
                                </button>
                            </div>
                            {!profile.watch_history || profile.watch_history.filter(h => h.action === 'saved').length === 0 ? (
                                <div className="text-center py-8 text-gray-400 italic">No saved places yet. Start saving venues!</div>
                            ) : (
                                <div className="grid grid-cols-2 gap-4">
                                    {profile.watch_history
                                        .filter(h => h.action === 'saved')
                                        .map((item, idx) => (
                                            <SavedPlaceCard key={idx} item={item} />
                                        ))}
                                </div>
                            )}
                        </div>

                        {/* Recent Activity */}
                        <div className="bg-white p-6 rounded-2xl shadow-sm">
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-bold text-lg flex items-center gap-2">
                                    <Clock className="w-5 h-5" />
                                    Recent Activity ({(profile.watch_history || []).length})
                                </h3>
                                <button
                                    onClick={async () => {
                                        if (confirm('Clear all activity for this user? This will help you test the feed changes.')) {
                                            try {
                                                await axios.post('http://localhost:8000/debug/clear-activity', {
                                                    user_id: selectedUserId
                                                });
                                                alert('Activity cleared! Refresh to see changes.');
                                                window.location.reload();
                                            } catch (e) {
                                                alert('Failed to clear activity');
                                            }
                                        }
                                    }}
                                    className="text-sm text-red-600 hover:text-red-700 font-medium"
                                >
                                    🗑️ Clear Activity
                                </button>
                            </div>
                            {!profile.watch_history || profile.watch_history.length === 0 ? (
                                <div className="text-center py-8 text-gray-400 italic">No activity yet</div>
                            ) : (
                                <div className="space-y-3">
                                    {profile.watch_history.slice(0, 10).map((item, idx) => (
                                        <WatchHistoryItem key={idx} item={item} />
                                    ))}
                                </div>
                            )}
                        </div>

                    </div>
                </div>
            )}
        </div>
    );
}

// Saved Place Card Component
function SavedPlaceCard({ item }) {
    const video = item.video || {};

    const getGradient = (categories) => {
        const gradients = {
            'cafe': 'from-purple-500 to-pink-500',
            'restaurant': 'from-orange-500 to-red-500',
            'bar': 'from-blue-500 to-cyan-500',
            'gallery': 'from-green-500 to-teal-500',
            'bakery': 'from-pink-500 to-yellow-500',
        };
        const category = categories?.[0] || 'restaurant';
        return gradients[category] || gradients['restaurant'];
    };

    return (
        <div className="border border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-shadow">
            <div className={`h-24 bg-gradient-to-br ${video.gradient || getGradient(video.categories)} relative`}>
                <div className="absolute bottom-2 left-2">
                    {video.categories?.slice(0, 2).map((cat, idx) => (
                        <span key={idx} className="inline-block px-2 py-1 bg-white/20 backdrop-blur text-white text-xs rounded mr-1">
                            {cat}
                        </span>
                    ))}
                </div>
            </div>
            <div className="p-4">
                {/* Video Title (primary) */}
                <h4 className="font-semibold text-gray-900 mb-1 truncate">
                    {video.title || 'Unknown Video'}
                </h4>
                {/* Venue Name (secondary) */}
                <div className="flex items-center gap-1 text-xs text-gray-500 mb-2">
                    <MapPin className="w-3 h-3" />
                    <span className="truncate">{video.venue_name || 'Unknown Venue'}</span>
                </div>
                <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                    {video.description || ''}
                </p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>📍 {video.neighborhood}</span>
                    <span className="px-2 py-0.5 bg-gray-100 rounded">{video.video_type}</span>
                </div>
            </div>
        </div>
    );
}

// Watch History Item Component
function WatchHistoryItem({ item }) {
    const video = item.video || {};

    const getActionIcon = (action) => {
        switch (action) {
            case 'shared': return <Share2 className="w-4 h-4 text-green-600" />;
            case 'saved': return <Bookmark className="w-4 h-4 text-blue-600" />;
            case 'viewed': return <Eye className="w-4 h-4 text-gray-600" />;
            case 'skipped': return <Eye className="w-4 h-4 text-red-400" />;
            default: return <Eye className="w-4 h-4 text-gray-400" />;
        }
    };

    const getActionColor = (action) => {
        switch (action) {
            case 'shared': return 'bg-green-50 text-green-700 border-green-200';
            case 'saved': return 'bg-blue-50 text-blue-700 border-blue-200';
            case 'viewed': return 'bg-gray-50 text-gray-700 border-gray-200';
            case 'skipped': return 'bg-red-50 text-red-700 border-red-200';
            default: return 'bg-gray-50 text-gray-700 border-gray-200';
        }
    };

    return (
        <div className={`border rounded-lg p-4 flex items-center gap-4 ${getActionColor(item.action)}`}>
            <div className="flex-shrink-0">
                {getActionIcon(item.action)}
            </div>

            <div className="flex-1 min-w-0">
                {/* Video Title (primary) */}
                <h4 className="font-semibold text-gray-900 truncate">
                    {video.title || item.video_title || 'Unknown Video'}
                </h4>
                {/* Venue Name (secondary) */}
                <div className="flex items-center gap-1 text-sm opacity-75 mb-1">
                    <MapPin className="w-3 h-3" />
                    <span className="truncate">{video.venue_name || item.venue_name || 'Unknown Venue'}</span>
                </div>
                <p className="text-sm opacity-75 truncate">
                    {video.description || ''}
                </p>
            </div>

            <div className="text-right flex-shrink-0">
                <div className="text-sm font-medium capitalize">{item.action}</div>
                <div className="text-xs opacity-75">{item.watch_time}s watched</div>
            </div>
        </div>
    );
}
