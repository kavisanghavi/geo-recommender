import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { User, MapPin, Heart, Check, Search, Plus } from 'lucide-react';
import clsx from 'clsx';

const INTERESTS = ["Italian", "Mexican", "Japanese", "Burgers", "Coffee", "Cocktails", "Jazz", "Techno", "Pop", "Rock", "Museums", "Parks", "Theater", "Sports"];

export default function CreateUser() {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);

    // Form Data
    const [user, setUser] = useState(null); // Created user object
    const [selectedInterests, setSelectedInterests] = useState([]);
    const [users, setUsers] = useState([]); // Existing users for friend selection
    const [venues, setVenues] = useState([]); // Venues for selection
    const [searchTerm, setSearchTerm] = useState('');

    // Step 1: Create Identity
    const createIdentity = async () => {
        setLoading(true);
        try {
            // We use the debug endpoint but pass interests
            const res = await axios.post('http://localhost:8000/debug/user', {
                interests: selectedInterests
            });
            setUser(res.data);
            setStep(2);
            fetchUsers(); // Pre-fetch for next step
        } catch (e) {
            alert("Failed to create user");
        } finally {
            setLoading(false);
        }
    };

    const toggleInterest = (interest) => {
        if (selectedInterests.includes(interest)) {
            setSelectedInterests(selectedInterests.filter(i => i !== interest));
        } else {
            setSelectedInterests([...selectedInterests, interest]);
        }
    };

    // Step 2: Add Friends
    const fetchUsers = async () => {
        const res = await axios.get('http://localhost:8000/debug/map-data');
        setUsers(res.data.users.filter(u => u.id !== user?.id));
    };

    const addFriend = async (friendId) => {
        try {
            await axios.post('http://localhost:8000/social/connect', {
                user_id_a: user.id,
                user_id_b: friendId
            });
            alert("Friend Added!");
        } catch (e) {
            alert("Failed to add friend");
        }
    };

    // Step 3: Add Places
    const fetchVenues = async () => {
        const res = await axios.get('http://localhost:8000/venues');
        setVenues(res.data.venues);
    };

    useEffect(() => {
        if (step === 3) fetchVenues();
    }, [step]);

    const interactVenue = async (venueId, type) => {
        try {
            await axios.post('http://localhost:8000/ingest/interaction', {
                user_id: user.id,
                venue_id: venueId,
                interaction_type: type,
                duration: 60
            });
            alert(`Marked as ${type}!`);
        } catch (e) {
            alert("Failed");
        }
    };

    return (
        <div className="h-full overflow-y-auto bg-gray-50 p-8">
            <div className="max-w-2xl mx-auto">
                {/* Progress */}
                <div className="flex items-center justify-between mb-8">
                    {[1, 2, 3].map(s => (
                        <div key={s} className="flex flex-col items-center">
                            <div className={clsx(
                                "w-10 h-10 rounded-full flex items-center justify-center font-bold transition-colors",
                                step >= s ? "bg-indigo-600 text-white" : "bg-gray-200 text-gray-500"
                            )}>
                                {s}
                            </div>
                            <span className="text-xs mt-2 font-medium text-gray-500">
                                {s === 1 ? 'Identity' : s === 2 ? 'Circle' : 'Taste'}
                            </span>
                        </div>
                    ))}
                    <div className="absolute top-12 left-0 w-full h-0.5 bg-gray-200 -z-10" />
                </div>

                {/* Step 1: Identity */}
                {step === 1 && (
                    <div className="bg-white p-8 rounded-2xl shadow-sm">
                        <h2 className="text-2xl font-bold mb-2">Create Persona</h2>
                        <p className="text-gray-500 mb-6">Define who this user is and what they like.</p>

                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-700 mb-2">Interests</label>
                            <div className="flex flex-wrap gap-2">
                                {INTERESTS.map(interest => (
                                    <button
                                        key={interest}
                                        onClick={() => toggleInterest(interest)}
                                        className={clsx(
                                            "px-4 py-2 rounded-full text-sm font-medium transition-colors border",
                                            selectedInterests.includes(interest)
                                                ? "bg-indigo-100 border-indigo-200 text-indigo-700"
                                                : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
                                        )}
                                    >
                                        {interest}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={createIdentity}
                            disabled={loading || selectedInterests.length === 0}
                            className="w-full bg-indigo-600 text-white py-3 rounded-xl font-bold hover:bg-indigo-700 disabled:opacity-50"
                        >
                            {loading ? 'Creating...' : 'Create User & Continue'}
                        </button>
                    </div>
                )}

                {/* Step 2: Circle */}
                {step === 2 && (
                    <div className="bg-white p-8 rounded-2xl shadow-sm">
                        <h2 className="text-2xl font-bold mb-2">Build Circle</h2>
                        <p className="text-gray-500 mb-6">Who is {user?.name} friends with?</p>

                        <div className="mb-4 relative">
                            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search users..."
                                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
                                onChange={e => setSearchTerm(e.target.value)}
                            />
                        </div>

                        <div className="h-64 overflow-y-auto space-y-2 mb-6">
                            {users.filter(u => u.name.toLowerCase().includes(searchTerm.toLowerCase())).map(u => (
                                <div key={u.id} className="flex items-center justify-between p-3 border border-gray-100 rounded-xl hover:bg-gray-50">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-xs font-bold">
                                            {u.name[0]}
                                        </div>
                                        <span className="font-medium">{u.name}</span>
                                    </div>
                                    <button
                                        onClick={() => addFriend(u.id)}
                                        className="text-indigo-600 hover:bg-indigo-50 p-2 rounded-full"
                                    >
                                        <Plus className="w-5 h-5" />
                                    </button>
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={() => setStep(3)}
                            className="w-full bg-indigo-600 text-white py-3 rounded-xl font-bold hover:bg-indigo-700"
                        >
                            Continue to Taste
                        </button>
                    </div>
                )}

                {/* Step 3: Taste */}
                {step === 3 && (
                    <div className="bg-white p-8 rounded-2xl shadow-sm">
                        <h2 className="text-2xl font-bold mb-2">Define Taste</h2>
                        <p className="text-gray-500 mb-6">Where does {user?.name} like to go?</p>

                        <div className="mb-4 relative">
                            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search places..."
                                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
                                onChange={e => setSearchTerm(e.target.value)}
                            />
                        </div>

                        <div className="h-64 overflow-y-auto space-y-2 mb-6">
                            {venues.filter(v => v.name.toLowerCase().includes(searchTerm.toLowerCase())).map(v => (
                                <div key={v.venue_id} className="flex items-center justify-between p-3 border border-gray-100 rounded-xl hover:bg-gray-50">
                                    <div>
                                        <div className="font-medium">{v.name}</div>
                                        <div className="text-xs text-gray-500">{v.category}</div>
                                    </div>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => interactVenue(v.venue_id, 'going')}
                                            className="px-3 py-1 bg-black text-white text-xs rounded-full hover:bg-gray-800"
                                        >
                                            Going
                                        </button>
                                        <button
                                            onClick={() => interactVenue(v.venue_id, 'saved')}
                                            className="px-3 py-1 border border-gray-300 text-xs rounded-full hover:bg-gray-100"
                                        >
                                            Save
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={() => navigate('/profiles')}
                            className="w-full bg-green-600 text-white py-3 rounded-xl font-bold hover:bg-green-700"
                        >
                            Finish & View Profile
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
