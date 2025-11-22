import React, { useState } from 'react';
import axios from 'axios';

export default function SimulationPanel({ onRefresh }) {
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState(null);
    const [friendId1, setFriendId1] = useState('');
    const [friendId2, setFriendId2] = useState('');

    const handleReset = async () => {
        if (!confirm("Are you sure? This will wipe all data.")) return;
        setLoading(true);
        try {
            await axios.post('http://localhost:8000/debug/reset');
            setMsg({ type: 'success', text: 'System Reset!' });
            onRefresh();
        } catch (e) {
            setMsg({ type: 'error', text: 'Reset failed' });
        } finally {
            setLoading(false);
        }
    };

    const handleCreateUser = async () => {
        setLoading(true);
        try {
            const res = await axios.post('http://localhost:8000/debug/user');
            setMsg({ type: 'success', text: `Created ${res.data.name}` });
            onRefresh();
        } catch (e) {
            setMsg({ type: 'error', text: 'Create failed' });
        } finally {
            setLoading(false);
        }
    };

    const handleAddFriend = async () => {
        if (!friendId1 || !friendId2) return;
        setLoading(true);
        try {
            await axios.post('http://localhost:8000/social/connect', {
                user_id_a: friendId1,
                user_id_b: friendId2
            });
            setMsg({ type: 'success', text: 'Connected!' });
            onRefresh();
        } catch (e) {
            setMsg({ type: 'error', text: 'Connection failed' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white p-4 border-t border-gray-200 shadow-lg">
            <h3 className="font-bold mb-2">Simulation Controls</h3>

            {msg && (
                <div className={`text-xs p-2 mb-2 rounded ${msg.type === 'success' ? 'bg-green-100' : 'bg-red-100'}`}>
                    {msg.text}
                </div>
            )}

            <div className="flex gap-2 mb-4">
                <button
                    onClick={handleCreateUser}
                    disabled={loading}
                    className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                >
                    + New User
                </button>
                <button
                    onClick={handleReset}
                    disabled={loading}
                    className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                >
                    Reset System
                </button>
            </div>

            <div className="border-t pt-2">
                <h4 className="text-xs font-bold mb-1">Connect Users</h4>
                <div className="flex gap-1 mb-2">
                    <input
                        type="text"
                        placeholder="User ID A"
                        className="border p-1 text-xs w-1/2"
                        value={friendId1}
                        onChange={e => setFriendId1(e.target.value)}
                    />
                    <input
                        type="text"
                        placeholder="User ID B"
                        className="border p-1 text-xs w-1/2"
                        value={friendId2}
                        onChange={e => setFriendId2(e.target.value)}
                    />
                </div>
                <button
                    onClick={handleAddFriend}
                    disabled={loading}
                    className="w-full bg-gray-800 text-white px-2 py-1 rounded text-xs hover:bg-gray-900"
                >
                    Add Friend Connection
                </button>
            </div>
        </div>
    );
}
