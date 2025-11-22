import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { ChevronUp, ChevronDown, Share2, Bookmark, Users, MapPin, TrendingUp, Target } from 'lucide-react';

export default function TikTokFeed({ userId }) {
    const [venues, setVenues] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [watchStartTime, setWatchStartTime] = useState(Date.now());
    const [loading, setLoading] = useState(true);
    const watchTimerRef = useRef(null);
    const watchStartTimeRef = useRef(Date.now());

    // Fetch feed
    useEffect(() => {
        if (!userId) return;

        const fetchFeed = async () => {
            try {
                // NYC Center coordinates
                const res = await axios.get(
                    `http://localhost:8000/feed?user_id=${userId}&lat=40.7128&lon=-74.0060&radius_km=2.0&limit=20`
                );
                setVenues(res.data.feed);
                setLoading(false);
            } catch (e) {
                console.error(e);
                setLoading(false);
            }
        };

        fetchFeed();
    }, [userId]);

    // Track watch time
    useEffect(() => {
        const startTime = Date.now();
        watchStartTimeRef.current = startTime;
        setWatchStartTime(startTime);

        // Clear any existing interval
        if (watchTimerRef.current) {
            clearInterval(watchTimerRef.current);
        }

        // Send watch time updates every 5 seconds
        watchTimerRef.current = setInterval(() => {
            const elapsed = Math.floor((Date.now() - watchStartTimeRef.current) / 1000);
            if (elapsed > 0 && venues[currentIndex]) {
                logEngagement(venues[currentIndex].venue_id, elapsed, 'view');
            }
        }, 5000);

        return () => {
            if (watchTimerRef.current) {
                clearInterval(watchTimerRef.current);
            }
        };
    }, [currentIndex, venues]);

    const logEngagement = async (venueId, watchTime, action) => {
        try {
            await axios.post('http://localhost:8000/engage', {
                user_id: userId,
                venue_id: venueId,
                watch_time_seconds: watchTime,
                action: action
            });
        } catch (e) {
            console.error('Failed to log engagement:', e);
        }
    };

    const handleSwipeNext = () => {
        const watchTime = Math.floor((Date.now() - watchStartTimeRef.current) / 1000);

        // Log skip if less than 3 seconds
        if (watchTime < 3 && venues[currentIndex]) {
            logEngagement(venues[currentIndex].venue_id, watchTime, 'skip');
        } else if (watchTime >= 3 && venues[currentIndex]) {
            // Log the final view time for this venue
            logEngagement(venues[currentIndex].venue_id, watchTime, 'view');
        }

        // Move to next venue
        if (currentIndex < venues.length - 1) {
            setCurrentIndex(currentIndex + 1);
        } else {
            // Loop back to start
            setCurrentIndex(0);
        }
    };

    const handleSwipePrevious = () => {
        if (currentIndex > 0) {
            setCurrentIndex(currentIndex - 1);
        }
    };

    const handleSave = async () => {
        const watchTime = Math.floor((Date.now() - watchStartTimeRef.current) / 1000);
        const venue = venues[currentIndex];

        await logEngagement(venue.venue_id, watchTime, 'save');
        alert('Saved! ✓');
    };

    const handleShare = async () => {
        const watchTime = Math.floor((Date.now() - watchStartTimeRef.current) / 1000);
        const venue = venues[currentIndex];

        // For demo, just log the share
        await logEngagement(venue.venue_id, watchTime, 'share');
        alert('Shared with friends! 🎉');
    };

    if (loading) {
        return (
            <div className="h-screen flex items-center justify-center bg-black text-white">
                <div className="text-center">
                    <div className="text-2xl mb-2">🎬</div>
                    <div>Curating your feed...</div>
                </div>
            </div>
        );
    }

    if (venues.length === 0) {
        return (
            <div className="h-screen flex items-center justify-center bg-black text-white">
                <div className="text-center">
                    <div className="text-2xl mb-2">📍</div>
                    <div>No venues found</div>
                </div>
            </div>
        );
    }

    const currentVenue = venues[currentIndex];

    // Generate a gradient background based on venue type
    const getGradientForVenue = (categories) => {
        const gradients = {
            'cafe': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'restaurant': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
            'bar': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            'gallery': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
            'bakery': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
            'coffee': 'linear-gradient(135deg, #30cfd0 0%, #330867 100%)',
        };
        const category = categories?.[0] || 'restaurant';
        return gradients[category] || gradients['restaurant'];
    };

    return (
        <div className="h-screen overflow-hidden bg-gray-900 flex">
            {/* Left Side - Venue Visual */}
            <div className="w-1/2 relative">
                {/* Background Gradient */}
                <div
                    className="w-full h-full"
                    style={{ background: getGradientForVenue(currentVenue.categories) }}
                />

                {/* Venue Info Overlay */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-black/50">
                    <div className="absolute top-6 left-6 right-6">
                        <div className="text-white text-sm opacity-75 mb-2">{currentIndex + 1} / {venues.length}</div>
                        <div className="flex gap-2">
                            <span className="px-3 py-1.5 bg-white/20 backdrop-blur rounded-lg text-white text-sm font-bold">
                                {currentVenue.neighborhood}
                            </span>
                            <span className="px-3 py-1.5 bg-white/20 backdrop-blur rounded-lg text-white text-sm">
                                {'$'.repeat(currentVenue.price_tier)}
                            </span>
                        </div>
                    </div>

                    <div className="absolute bottom-6 left-6 right-6 text-white">
                        <h1 className="text-4xl font-bold mb-3">{currentVenue.name}</h1>
                        <p className="text-base opacity-90 mb-4">{currentVenue.description}</p>
                        <div className="flex gap-2">
                            {currentVenue.categories.slice(0, 3).map((cat, idx) => (
                                <span key={idx} className="px-3 py-1 bg-white/20 backdrop-blur rounded-lg text-sm">
                                    {cat}
                                </span>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Navigation Buttons */}
                <div className="absolute left-6 top-1/2 -translate-y-1/2 flex flex-col gap-3 z-20">
                    <button
                        onClick={handleSwipePrevious}
                        disabled={currentIndex === 0}
                        className="w-14 h-14 rounded-full bg-white/90 flex items-center justify-center text-gray-900 disabled:opacity-30 hover:bg-white transition shadow-lg"
                    >
                        <ChevronUp className="w-6 h-6" />
                    </button>
                    <button
                        onClick={handleSwipeNext}
                        className="w-14 h-14 rounded-full bg-white/90 flex items-center justify-center text-gray-900 hover:bg-white transition shadow-lg"
                    >
                        <ChevronDown className="w-6 h-6" />
                    </button>
                </div>
            </div>

            {/* Right Side - Algorithm Details */}
            <div className="w-1/2 bg-white overflow-y-auto">
                <div className="p-8">
                    {/* Action Buttons */}
                    <div className="flex gap-3 mb-6">
                        <button
                            onClick={handleSave}
                            className="flex-1 flex items-center justify-center gap-2 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition"
                        >
                            <Bookmark className="w-5 h-5" />
                            Save
                        </button>
                        <button
                            onClick={handleShare}
                            className="flex-1 flex items-center justify-center gap-2 py-3 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition"
                        >
                            <Share2 className="w-5 h-5" />
                            Share
                        </button>
                    </div>

                    {/* Algorithm Explanation */}
                    <AlgorithmBreakdown explanation={currentVenue.explanation} finalScore={currentVenue.final_score} />
                </div>
            </div>
        </div>
    );
}

// Algorithm Breakdown Component
function AlgorithmBreakdown({ explanation, finalScore }) {
    if (!explanation) return null;

    return (
        <div className="space-y-6">
            {/* Final Score */}
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6 rounded-2xl">
                <div className="text-sm font-medium opacity-90 mb-1">Final Match Score</div>
                <div className="text-5xl font-bold mb-3">{Math.round(finalScore * 100)}%</div>
                <div className="text-xs opacity-75 mb-2">
                    Formula: (0.3 × Taste) + (0.4 × Social) + (0.2 × Proximity) + (0.1 × Trending)
                </div>
                <div className="text-xs bg-white/20 rounded p-2 mt-2">
                    ⏱️ Watch Time Filter: Only friends who watched ≥10s count toward Social score
                </div>
            </div>

            {/* Component Scores */}
            <div className="space-y-4">
                {/* Taste Match */}
                <div className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                            <Target className="w-5 h-5 text-blue-600" />
                            <span className="font-bold text-gray-900">Taste Match</span>
                        </div>
                        <span className="text-2xl font-bold text-blue-600">{Math.round(explanation.taste_match.score * 100)}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
                        <div className="h-full bg-blue-500" style={{ width: `${explanation.taste_match.score * 100}%` }} />
                    </div>
                    <p className="text-sm text-gray-600">{explanation.taste_match.reason}</p>
                    <p className="text-xs text-gray-500 mt-1">Weight: 30%</p>
                </div>

                {/* Social Proof */}
                <div className="border-l-4 border-indigo-500 pl-4 py-2">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                            <Users className="w-5 h-5 text-indigo-600" />
                            <span className="font-bold text-gray-900">Friend Activity</span>
                        </div>
                        <span className="text-2xl font-bold text-indigo-600">{Math.round(explanation.social_proof.score * 100)}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
                        <div className="h-full bg-indigo-500" style={{ width: `${explanation.social_proof.score * 100}%` }} />
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{explanation.social_proof.reason}</p>
                    <div className="text-xs bg-indigo-50 p-2 rounded mb-2 border border-indigo-200">
                        <span className="font-semibold">⏱️ Watch Time Quality Filter:</span> Shared (+15), Saved (+8), Watched 10s+ (+5), Mutuals (+2)
                    </div>
                    {explanation.social_proof.contributors.length > 0 && (
                        <div className="mt-2 space-y-1">
                            {explanation.social_proof.contributors.map((c, idx) => (
                                <div key={idx} className="flex justify-between items-center text-sm bg-indigo-50 p-2 rounded">
                                    <span className="text-gray-700">
                                        {c.friend ? (
                                            <>
                                                {c.friend}{' '}
                                                {c.action === 'shared' && '📤 shared'}
                                                {c.action === 'saved' && '💾 saved'}
                                                {c.action === 'viewed' && '👀 watched ≥10s'}
                                            </>
                                        ) : (
                                            `${c.mutuals} mutual friends interested`
                                        )}
                                    </span>
                                    <span className="text-green-600 font-bold">+{c.boost} pts</span>
                                </div>
                            ))}
                        </div>
                    )}
                    <p className="text-xs text-gray-500 mt-2">Weight: 40% (highest weight component)</p>
                </div>

                {/* Proximity */}
                <div className="border-l-4 border-green-500 pl-4 py-2">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                            <MapPin className="w-5 h-5 text-green-600" />
                            <span className="font-bold text-gray-900">Proximity</span>
                        </div>
                        <span className="text-2xl font-bold text-green-600">{Math.round(explanation.proximity.score * 100)}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
                        <div className="h-full bg-green-500" style={{ width: `${explanation.proximity.score * 100}%` }} />
                    </div>
                    <p className="text-sm text-gray-600">{explanation.proximity.reason}</p>
                    <p className="text-xs text-gray-500 mt-1">Weight: 20%</p>
                </div>

                {/* Trending */}
                <div className="border-l-4 border-orange-500 pl-4 py-2">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-orange-600" />
                            <span className="font-bold text-gray-900">Trending</span>
                        </div>
                        <span className="text-2xl font-bold text-orange-600">{Math.round(explanation.trending.score * 100)}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-2">
                        <div className="h-full bg-orange-500" style={{ width: `${explanation.trending.score * 100}%` }} />
                    </div>
                    <p className="text-sm text-gray-600">{explanation.trending.reason}</p>
                    <p className="text-xs text-gray-500 mt-1">Weight: 10%</p>
                </div>
            </div>
        </div>
    );
}
