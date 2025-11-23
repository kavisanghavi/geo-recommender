import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { UserPlus, Users, Clock, Share2, Bookmark, Eye, X } from 'lucide-react';

export default function UserProfileEnhanced({ userId }) {
    const [profile, setProfile] = useState(null);
    const [allUsers, setAllUsers] = useState([]);
    const [showAddFriend, setShowAddFriend] = useState(false);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!userId) return;
        fetchProfile();
    }, [userId]);

    const fetchProfile = async () => {
        try {
            const res = await axios.get(`http://localhost:8000/user/${userId}`);
            setProfile(res.data);
            setLoading(false);
        } catch (e) {
            console.error(e);
            setLoading(false);
        }
    };

    const fetchAllUsers = async () => {
        try {
            const res = await axios.get(`http://localhost:8000/users?current_user_id=${userId}`);
            setAllUsers(res.data.users);
        } catch (e) {
            console.error(e);
        }
    };

    const handleAddFriend = async (friendId) => {
        try {
            await axios.post('http://localhost:8000/friends/add', {
                user_id: userId,
                friend_id: friendId
            });
            // Refresh profile
            await fetchProfile();
            alert('Friend added! ✓');
        } catch (e) {
            alert('Failed to add friend');
        }
    };

    if (loading) {
        return (
            <div className="h-full flex items-center justify-center">
                <div>Loading profile...</div>
            </div>
        );
    }

    if (!profile) {
        return (
            <div className="h-full flex items-center justify-center">
                <div>User not found</div>
            </div>
        );
    }

    const filteredUsers = allUsers.filter(u =>
        u.name.toLowerCase().includes(search.toLowerCase()) &&
        !u.is_friend &&
        !u.is_self
    );

    return (
        <div className="h-full overflow-y-auto bg-gray-50">
            <div className="max-w-4xl mx-auto p-6 space-y-6">
                {/* Profile Header */}
                <div className="bg-white rounded-2xl p-6 shadow-sm">
                    <div className="flex items-start justify-between mb-4">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 mb-1">
                                {profile.user.name}
                            </h1>
                            <p className="text-indigo-600 font-medium">
                                {profile.user.archetype}
                            </p>
                        </div>
                        <div className="text-right">
                            <div className="text-2xl font-bold text-gray-900">
                                {profile.friends.length}
                            </div>
                            <div className="text-sm text-gray-500">Friends</div>
                        </div>
                    </div>

                    {/* Interests */}
                    <div className="mb-4">
                        <h3 className="text-sm font-semibold text-gray-700 mb-2">Interests</h3>
                        <div className="flex flex-wrap gap-2">
                            {profile.user.interests.map((interest, idx) => (
                                <span
                                    key={idx}
                                    className="px-3 py-1 bg-indigo-50 text-indigo-700 rounded-full text-sm"
                                >
                                    {interest}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Friends Section */}
                <div className="bg-white rounded-2xl p-6 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                            <Users className="w-5 h-5" />
                            Friends ({profile.friends.length})
                        </h2>
                        <button
                            onClick={() => {
                                fetchAllUsers();
                                setShowAddFriend(true);
                            }}
                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
                        >
                            <UserPlus className="w-4 h-4" />
                            Add Friends
                        </button>
                    </div>

                    {profile.friends.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            No friends yet. Add some to see social recommendations!
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 gap-3">
                            {profile.friends.map(friend => (
                                <FriendCard key={friend.id} friend={friend} />
                            ))}
                        </div>
                    )}
                </div>

                {/* My Places (Saved Venues) */}
                <div className="bg-white rounded-2xl p-6 shadow-sm">
                    <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2 mb-4">
                        <Bookmark className="w-5 h-5 text-blue-600" />
                        My Places ({profile.watch_history?.filter(h => h.action === 'saved').length || 0})
                    </h2>

                    {!profile.watch_history || profile.watch_history.filter(h => h.action === 'saved').length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            No saved places yet. Start saving venues you want to visit!
                        </div>
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

                {/* Watch History */}
                <div className="bg-white rounded-2xl p-6 shadow-sm">
                    <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2 mb-4">
                        <Clock className="w-5 h-5" />
                        Recent Activity ({profile.watch_history?.length || 0})
                    </h2>

                    {!profile.watch_history || profile.watch_history.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            No activity yet
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {profile.watch_history.slice(0, 10).map((item, idx) => (
                                <WatchHistoryItem key={idx} item={item} />
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Add Friend Modal */}
            {showAddFriend && (
                <AddFriendModal
                    search={search}
                    setSearch={setSearch}
                    users={filteredUsers}
                    onAdd={handleAddFriend}
                    onClose={() => setShowAddFriend(false)}
                />
            )}
        </div>
    );
}

// Friend Card Component
function FriendCard({ friend }) {
    return (
        <div className="border border-gray-200 rounded-xl p-4 hover:border-indigo-300 transition">
            <div className="flex items-start justify-between">
                <div>
                    <h3 className="font-semibold text-gray-900">{friend.name}</h3>
                    <div className="flex flex-wrap gap-1 mt-2">
                        {friend.interests?.slice(0, 3).map((interest, idx) => (
                            <span
                                key={idx}
                                className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                            >
                                {interest}
                            </span>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

// Saved Place Card Component
function SavedPlaceCard({ item }) {
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
            <div className={`h-24 bg-gradient-to-br ${getGradient(item.venue?.categories)} relative`}>
                <div className="absolute bottom-2 left-2">
                    {item.venue?.categories?.slice(0, 2).map((cat, idx) => (
                        <span key={idx} className="inline-block px-2 py-1 bg-white/20 backdrop-blur text-white text-xs rounded mr-1">
                            {cat}
                        </span>
                    ))}
                </div>
            </div>
            <div className="p-4">
                <h4 className="font-semibold text-gray-900 mb-1 truncate">
                    {item.venue?.name || 'Unknown Venue'}
                </h4>
                <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                    {item.venue?.description || ''}
                </p>
                <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>📍 {item.venue?.neighborhood}</span>
                    <span>{'$'.repeat(item.venue?.price_tier || 1)}</span>
                </div>
            </div>
        </div>
    );
}

// Watch History Item Component
function WatchHistoryItem({ item }) {
    const getActionIcon = (action) => {
        switch (action) {
            case 'shared': return <Share2 className="w-4 h-4 text-green-600" />;
            case 'saved': return <Bookmark className="w-4 h-4 text-blue-600" />;
            case 'viewed': return <Eye className="w-4 h-4 text-gray-600" />;
            default: return <Eye className="w-4 h-4 text-gray-400" />;
        }
    };

    const getActionColor = (action) => {
        switch (action) {
            case 'shared': return 'bg-green-50 text-green-700 border-green-200';
            case 'saved': return 'bg-blue-50 text-blue-700 border-blue-200';
            case 'viewed': return 'bg-gray-50 text-gray-700 border-gray-200';
            default: return 'bg-gray-50 text-gray-700 border-gray-200';
        }
    };

    return (
        <div className={`border rounded-lg p-4 flex items-center gap-4 ${getActionColor(item.action)}`}>
            <div className="flex-shrink-0">
                {getActionIcon(item.action)}
            </div>

            <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-gray-900 truncate">
                    {item.venue?.name || 'Unknown Venue'}
                </h4>
                <p className="text-sm opacity-75 truncate">
                    {item.venue?.description || ''}
                </p>
            </div>

            <div className="text-right flex-shrink-0">
                <div className="text-sm font-medium capitalize">{item.action}</div>
                <div className="text-xs opacity-75">{item.watch_time}s watched</div>
            </div>
        </div>
    );
}

// Add Friend Modal Component
function AddFriendModal({ search, setSearch, users, onAdd, onClose }) {
    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl">
                {/* Header */}
                <div className="p-6 border-b flex items-center justify-between">
                    <h2 className="text-2xl font-bold text-gray-900">Add Friends</h2>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-lg transition"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Search */}
                <div className="p-6 border-b">
                    <input
                        type="text"
                        placeholder="Search users..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                </div>

                {/* User List */}
                <div className="flex-1 overflow-y-auto p-6">
                    {users.length === 0 ? (
                        <div className="text-center py-12 text-gray-500">
                            No users found
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {users.map(user => (
                                <div
                                    key={user.id}
                                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-indigo-300 transition"
                                >
                                    <div>
                                        <h3 className="font-semibold text-gray-900">{user.name}</h3>
                                        <p className="text-sm text-indigo-600">{user.archetype}</p>
                                        <div className="flex flex-wrap gap-1 mt-1">
                                            {user.interests?.slice(0, 3).map((interest, idx) => (
                                                <span
                                                    key={idx}
                                                    className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                                                >
                                                    {interest}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => onAdd(user.id)}
                                        className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition flex items-center gap-2"
                                    >
                                        <UserPlus className="w-4 h-4" />
                                        Add
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
