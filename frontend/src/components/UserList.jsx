import React, { useState } from 'react';
import axios from 'axios';

export default function UserList({ users, selectedUserId, onSelectUser, onRefresh }) {
    const [loading, setLoading] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [friendMode, setFriendMode] = useState(null); // null or userId of user we are adding friend TO

    const filteredUsers = users.filter(u =>
        u.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        u.id.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleCreateUser = async () => {
        setLoading(true);
        try {
            await axios.post('http://localhost:8000/debug/user');
            onRefresh();
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleReset = async () => {
        if (!confirm("Reset Users & Interactions? (Venues will be preserved)")) return;
        setLoading(true);
        try {
            await axios.post('http://localhost:8000/debug/reset?clear_venues=false');
            onRefresh();
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const initiateAddFriend = (e, userId) => {
        e.stopPropagation();
        setFriendMode(userId);
    };

    const confirmAddFriend = async (e, targetUserId) => {
        e.stopPropagation();
        if (!friendMode) return;
        setLoading(true);
        try {
            await axios.post('http://localhost:8000/social/connect', {
                user_id_a: friendMode,
                user_id_b: targetUserId
            });
            alert("Connected!");
            setFriendMode(null);
            onRefresh(); // Refresh to show updated graph if we visualized it, or just to be safe
        } catch (e) {
            console.error(e);
            alert("Failed to connect");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white border-r border-gray-200">
            {/* Header / Controls */}
            <div className="p-4 border-b border-gray-200 bg-gray-50">
                <h2 className="font-bold text-lg mb-2">Users ({users.length})</h2>
                <div className="flex gap-2 mb-2">
                    <button
                        onClick={handleCreateUser}
                        disabled={loading}
                        className="flex-1 bg-blue-600 text-white py-1 px-2 rounded text-sm hover:bg-blue-700"
                    >
                        + New User
                    </button>
                    <button
                        onClick={handleReset}
                        disabled={loading}
                        className="bg-red-100 text-red-600 py-1 px-2 rounded text-sm hover:bg-red-200"
                    >
                        Reset
                    </button>
                </div>
                <input
                    type="text"
                    placeholder="Search users..."
                    className="w-full border p-1 rounded text-sm"
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                />
            </div>

            {/* Friend Mode Banner */}
            {friendMode && (
                <div className="bg-yellow-100 p-2 text-xs text-yellow-800 flex justify-between items-center">
                    <span>Select a friend for <b>{users.find(u => u.id === friendMode)?.name}</b></span>
                    <button onClick={() => setFriendMode(null)} className="font-bold">X</button>
                </div>
            )}

            {/* List */}
            <div className="flex-1 overflow-y-auto">
                {filteredUsers.map(user => (
                    <div
                        key={user.id}
                        onClick={() => onSelectUser(user.id)}
                        className={`p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition
                            ${selectedUserId === user.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''}
                        `}
                    >
                        <div className="flex justify-between items-start">
                            <div>
                                <div className="font-medium text-sm">{user.name}</div>
                                <div className="text-xs text-gray-400">{user.id}</div>
                            </div>
                            {friendMode && friendMode !== user.id && (
                                <button
                                    onClick={(e) => confirmAddFriend(e, user.id)}
                                    className="bg-green-500 text-white text-xs px-2 py-1 rounded"
                                >
                                    Select
                                </button>
                            )}
                            {!friendMode && (
                                <button
                                    onClick={(e) => initiateAddFriend(e, user.id)}
                                    className="text-gray-400 hover:text-blue-500"
                                    title="Add Friend"
                                >
                                    +👤
                                </button>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
