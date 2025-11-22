import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { User, MapPin, Users, Heart, Calendar } from 'lucide-react';

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

                        {/* Two Columns: Friends & Places */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Friends */}
                            <div className="bg-white p-6 rounded-2xl shadow-sm">
                                <h3 className="font-bold text-lg mb-4">Friends</h3>
                                <div className="space-y-3">
                                    {(profile.friends || []).map(f => (
                                        <div key={f.id} className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded-lg">
                                            <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-xs font-bold">
                                                {f.name[0]}
                                            </div>
                                            <span className="font-medium">{f.name}</span>
                                        </div>
                                    ))}
                                    {(profile.friends || []).length === 0 && <div className="text-gray-400 italic">No friends yet</div>}
                                </div>
                            </div>

                            {/* Places */}
                            <div className="bg-white p-6 rounded-2xl shadow-sm">
                                <h3 className="font-bold text-lg mb-4">My Places</h3>
                                <div className="space-y-3">
                                    {(profile.interactions || []).map((interaction, i) => (
                                        <div key={i} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded-lg border border-gray-100">
                                            <div>
                                                <div className="font-medium">{interaction.venue?.name || interaction.venue_id}</div>
                                                <div className="text-xs text-gray-500">{interaction.venue?.category}</div>
                                            </div>
                                            <span className={interaction.type === 'going' ? 'text-green-600 text-xs font-bold' : 'text-blue-600 text-xs font-bold'}>
                                                {interaction.type.toUpperCase()}
                                            </span>
                                        </div>
                                    ))}
                                    {(profile.interactions || []).length === 0 && <div className="text-gray-400 italic">No places yet</div>}
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            )}
        </div>
    );
}
