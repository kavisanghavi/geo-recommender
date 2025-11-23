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
    const [userName, setUserName] = useState(''); // User's name
    const [selectedInterests, setSelectedInterests] = useState([]);
    const [selectedFriends, setSelectedFriends] = useState([]); // Track selected friends
    const [users, setUsers] = useState([]); // Existing users for friend selection
    const [venues, setVenues] = useState([]); // Venues for selection
    const [searchTerm, setSearchTerm] = useState('');

    // Step 1: Create Identity
    const createIdentity = async () => {
        setLoading(true);
        try {
            // We use the debug endpoint but pass name and interests
            const nameValue = userName.trim();
            const payload = {
                interests: selectedInterests
            };
            // Only include name if it's not empty, otherwise backend generates random name
            if (nameValue) {
                payload.name = nameValue;
            }

            console.log('Creating user with payload:', payload);
            const res = await axios.post('http://localhost:8000/debug/user', payload);
            const newUser = res.data;
            console.log('User created:', newUser);
            setUser(newUser);
            setStep(2);
            // Fetch users for friend selection, excluding the newly created user
            await fetchUsersExcluding(newUser.id);
        } catch (e) {
            console.error('Failed to create user:', e);
            alert("Failed to create user: " + (e.response?.data?.detail || e.message));
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
    const fetchUsersExcluding = async (excludeUserId) => {
        try {
            const res = await axios.get('http://localhost:8000/debug/map-data');
            // Filter out the specified user to prevent self-friending
            const filteredUsers = res.data.users.filter(u => u.id !== excludeUserId);
            console.log('Fetched users for friend selection:', filteredUsers.length, 'users (excluding', excludeUserId, ')');
            setUsers(filteredUsers);
        } catch (error) {
            console.error('Failed to fetch users:', error);
            alert('Failed to load users. Please try again.');
        }
    };

    const addFriend = async (friendId) => {
        try {
            await axios.post('http://localhost:8000/social/connect', {
                user_id_a: user.id,
                user_id_b: friendId
            });
            setSelectedFriends([...selectedFriends, friendId]);
        } catch (e) {
            alert("Failed to add friend");
        }
    };

    // Step 3: Add Places
    const fetchVenues = async () => {
        try {
            console.log('Fetching venues for Define Taste step...');
            const res = await axios.get('http://localhost:8000/venues-with-videos?limit=30');
            console.log('Venues fetched:', res.data.venues.length, 'venues');
            setVenues(res.data.venues);
        } catch (error) {
            console.error('Failed to fetch venues:', error);
            alert('Failed to load venues. Please try again.');
        }
    };

    useEffect(() => {
        if (step === 3) fetchVenues();
    }, [step]);

    const [videoInteractions, setVideoInteractions] = useState({}); // Track interactions per video

    const interactVideo = async (videoId, action) => {
        try {
            await axios.post('http://localhost:8000/engage-video', {
                user_id: user.id,
                video_id: videoId,
                action: action,
                watch_time: action === 'viewed' ? 15 : 0
            });
            setVideoInteractions({
                ...videoInteractions,
                [videoId]: action
            });
        } catch (e) {
            alert("Failed to engage with video");
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
                            <label className="block text-sm font-medium text-gray-700 mb-2">Name (optional)</label>
                            <input
                                type="text"
                                placeholder="Leave blank for random name"
                                value={userName}
                                onChange={(e) => setUserName(e.target.value)}
                                className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
                            />
                            <p className="text-xs text-gray-500 mt-1">If left blank, a random name will be generated</p>
                        </div>

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
                            {users.filter(u => u.name.toLowerCase().includes(searchTerm.toLowerCase())).map(u => {
                                const isSelected = selectedFriends.includes(u.id);
                                return (
                                    <div key={u.id} className={clsx(
                                        "flex items-center justify-between p-3 border rounded-xl transition",
                                        isSelected ? "bg-indigo-50 border-indigo-300" : "border-gray-100 hover:bg-gray-50"
                                    )}>
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center text-xs font-bold">
                                                {u.name[0]}
                                            </div>
                                            <span className="font-medium">{u.name}</span>
                                        </div>
                                        <button
                                            onClick={() => addFriend(u.id)}
                                            disabled={isSelected}
                                            className={clsx(
                                                "p-2 rounded-full transition",
                                                isSelected
                                                    ? "text-green-600 bg-green-50 cursor-not-allowed"
                                                    : "text-indigo-600 hover:bg-indigo-50"
                                            )}
                                        >
                                            {isSelected ? <Check className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
                                        </button>
                                    </div>
                                );
                            })}
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
                        <p className="text-gray-500 mb-6">What videos does {user?.name} like?</p>

                        <div className="mb-4 relative">
                            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search places..."
                                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
                                onChange={e => setSearchTerm(e.target.value)}
                            />
                        </div>

                        <div className="h-80 overflow-y-auto space-y-3 mb-6">
                            {venues.length === 0 ? (
                                <div className="text-center py-12 text-gray-400">
                                    <p className="mb-2">Loading venues...</p>
                                    <p className="text-xs">If this persists, check the console for errors</p>
                                </div>
                            ) : venues.filter(v => v.name && v.name.toLowerCase().includes(searchTerm.toLowerCase())).length === 0 ? (
                                <div className="text-center py-12 text-gray-400">
                                    <p>No venues found matching "{searchTerm}"</p>
                                </div>
                            ) : (
                                venues.filter(v => v.name && v.name.toLowerCase().includes(searchTerm.toLowerCase())).map(v => (
                                    <div key={v.venue_id} className="border border-gray-200 rounded-xl p-3">
                                        <div className="mb-2">
                                            <div className="font-semibold text-gray-900">{v.name}</div>
                                            <div className="text-xs text-gray-500">{v.category}</div>
                                        </div>

                                        {/* Videos for this venue */}
                                        <div className="space-y-2">
                                            {v.videos && v.videos.length > 0 ? (
                                                v.videos.map(video => {
                                                const interaction = videoInteractions[video.id];
                                                return (
                                                    <div key={video.id} className="bg-gray-50 p-2 rounded-lg">
                                                        <div className="text-sm font-medium text-gray-800 mb-1">{video.title}</div>
                                                        <div className="text-xs text-gray-600 mb-2 line-clamp-1">{video.description}</div>
                                                        <div className="flex gap-2">
                                                            <button
                                                                onClick={() => interactVideo(video.id, 'viewed')}
                                                                className={clsx(
                                                                    "px-3 py-1 text-xs rounded-full transition border",
                                                                    interaction === 'viewed'
                                                                        ? "bg-indigo-100 border-indigo-300 text-indigo-700"
                                                                        : "border-gray-300 text-gray-700 hover:bg-gray-100"
                                                                )}
                                                            >
                                                                {interaction === 'viewed' ? '✓ Watched' : 'Watch'}
                                                            </button>
                                                            <button
                                                                onClick={() => interactVideo(video.id, 'saved')}
                                                                className={clsx(
                                                                    "px-3 py-1 text-xs rounded-full transition border",
                                                                    interaction === 'saved'
                                                                        ? "bg-blue-100 border-blue-300 text-blue-700"
                                                                        : "border-gray-300 text-gray-700 hover:bg-gray-100"
                                                                )}
                                                            >
                                                                {interaction === 'saved' ? '✓ Saved' : 'Save'}
                                                            </button>
                                                            <button
                                                                onClick={() => interactVideo(video.id, 'shared')}
                                                                className={clsx(
                                                                    "px-3 py-1 text-xs rounded-full transition border",
                                                                    interaction === 'shared'
                                                                        ? "bg-green-100 border-green-300 text-green-700"
                                                                        : "border-gray-300 text-gray-700 hover:bg-gray-100"
                                                                )}
                                                            >
                                                                {interaction === 'shared' ? '✓ Shared' : 'Share'}
                                                            </button>
                                                        </div>
                                                    </div>
                                                );
                                            })
                                        ) : (
                                            <div className="text-xs text-gray-400 italic">No videos available</div>
                                        )}
                                    </div>
                                </div>
                                ))
                            )}
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
