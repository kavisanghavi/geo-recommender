import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { ChevronUp, ChevronDown, Share2, Bookmark, Users, MapPin, TrendingUp, Target, Info } from 'lucide-react';

export default function ShortVideoFeed({ userId }) {
    const [venues, setVenues] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [watchStartTime, setWatchStartTime] = useState(Date.now());
    const [loading, setLoading] = useState(true);
    const [saved, setSaved] = useState(false);
    const [shared, setShared] = useState(false);
    const watchTimerRef = useRef(null);
    const watchStartTimeRef = useRef(Date.now());

    // Debug log
    console.log('ShortVideoFeed loaded with userId:', userId);

    // Fetch video feed
    useEffect(() => {
        if (!userId) return;

        const fetchFeed = async () => {
            try {
                // NYC Center coordinates - now fetching VIDEOS not venues
                const res = await axios.get(
                    `http://localhost:8000/feed-video?user_id=${userId}&lat=40.7128&lon=-74.0060&radius_km=2.0&limit=20`
                );
                setVenues(res.data.feed); // Still called 'venues' in state but contains video objects
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

        // Reset saved/shared state for new video
        setSaved(false);
        setShared(false);

        // Clear any existing interval
        if (watchTimerRef.current) {
            clearInterval(watchTimerRef.current);
        }

        // Send watch time updates every 5 seconds
        watchTimerRef.current = setInterval(() => {
            const elapsed = Math.floor((Date.now() - watchStartTimeRef.current) / 1000);
            if (elapsed > 0 && venues[currentIndex]) {
                logEngagement(venues[currentIndex].video_id, elapsed, 'view');
            }
        }, 5000);

        return () => {
            if (watchTimerRef.current) {
                clearInterval(watchTimerRef.current);
            }
        };
    }, [currentIndex, venues]);

    const logEngagement = async (videoId, watchTime, action) => {
        try {
            const payload = {
                user_id: userId,
                video_id: videoId,
                watch_time_seconds: watchTime,
                action: action
            };
            console.log('Logging engagement:', payload);
            const response = await axios.post('http://localhost:8000/engage-video', payload);
            console.log('Engagement logged successfully:', response.data);
        } catch (e) {
            console.error('Failed to log engagement:', e);
            throw e; // Re-throw so handleSave/handleShare can catch it
        }
    };

    const handleSwipeNext = () => {
        const watchTime = Math.floor((Date.now() - watchStartTimeRef.current) / 1000);

        // Log skip if less than 3 seconds
        if (watchTime < 3 && venues[currentIndex]) {
            logEngagement(venues[currentIndex].video_id, watchTime, 'skip');
        } else if (watchTime >= 3 && venues[currentIndex]) {
            // Log the final view time for this video
            logEngagement(venues[currentIndex].video_id, watchTime, 'view');
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
        try {
            const watchTime = Math.floor((Date.now() - watchStartTimeRef.current) / 1000);
            const video = venues[currentIndex];

            console.log('💾 SAVE BUTTON CLICKED! Video:', video.video_id, 'watch time:', watchTime);
            setSaved(true);
            await logEngagement(video.video_id, watchTime, 'save');
            console.log('✅ Save successful!');
            alert('✓ Saved! Check the console for details.');
        } catch (error) {
            console.error('❌ Save failed:', error);
            setSaved(false);
            alert('❌ Failed to save video. Check console for details.');
        }
    };

    const handleShare = async () => {
        try {
            const watchTime = Math.floor((Date.now() - watchStartTimeRef.current) / 1000);
            const video = venues[currentIndex];

            console.log('📤 SHARE BUTTON CLICKED! Video:', video.video_id, 'watch time:', watchTime);
            setShared(true);
            await logEngagement(video.video_id, watchTime, 'share');
            console.log('✅ Share successful!');
            alert('🎉 Shared with friends! Check the console for details.');
        } catch (error) {
            console.error('❌ Share failed:', error);
            setShared(false);
            alert('❌ Failed to share video. Check console for details.');
        }
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
                        {/* Video Title (larger, more prominent) */}
                        <h1 className="text-3xl font-bold mb-2">{currentVenue.title}</h1>
                        {/* Venue Name (smaller, secondary) */}
                        <div className="flex items-center gap-2 mb-3">
                            <MapPin className="w-4 h-4 opacity-75" />
                            <p className="text-lg opacity-90 font-medium">{currentVenue.name}</p>
                        </div>
                        <p className="text-sm opacity-80 mb-4">{currentVenue.description}</p>
                        <div className="flex gap-2">
                            {currentVenue.categories.slice(0, 3).map((cat, idx) => (
                                <span key={idx} className="px-3 py-1 bg-white/20 backdrop-blur rounded-lg text-xs">
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
                            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-semibold transition ${saved
                                    ? 'bg-green-600 text-white'
                                    : 'bg-blue-600 text-white hover:bg-blue-700'
                                }`}
                        >
                            <Bookmark className="w-5 h-5" />
                            {saved ? '✓ Saved' : 'Save'}
                        </button>
                        <button
                            onClick={handleShare}
                            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-semibold transition ${shared
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-green-600 text-white hover:bg-green-700'
                                }`}
                        >
                            <Share2 className="w-5 h-5" />
                            {shared ? '✓ Shared' : 'Share'}
                        </button>
                    </div>

                    {/* Algorithm Explanation */}
                    <AlgorithmBreakdown explanation={currentVenue.explanation} finalScore={currentVenue.final_score} />
                </div>
            </div>
        </div>
    );
}

// Tooltip Component
function Tooltip({ children, content }) {
    const [isVisible, setIsVisible] = useState(false);

    return (
        <div className="relative inline-block">
            <div
                onMouseEnter={() => setIsVisible(true)}
                onMouseLeave={() => setIsVisible(false)}
                className="cursor-help"
            >
                {children}
            </div>
            {isVisible && (
                <div className="absolute z-50 w-64 p-3 text-xs bg-gray-900 text-white rounded-lg shadow-lg -top-2 left-8 transform -translate-y-full">
                    <div className="absolute top-full left-4 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                    {content}
                </div>
            )}
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
                            <Tooltip content={
                                <div>
                                    <div className="font-semibold mb-1">Taste Match - 30% Weight</div>
                                    <div className="text-xs opacity-90">
                                        Measures how well this video matches your interests based on:
                                        <ul className="list-disc ml-4 mt-1">
                                            <li>Your saved interests and preferences</li>
                                            <li>Categories you engage with most</li>
                                            <li>Similar venues you've enjoyed</li>
                                        </ul>
                                        Higher score = closer match to your taste profile
                                    </div>
                                </div>
                            }>
                                <Info className="w-4 h-4 text-gray-400 hover:text-blue-600 transition" />
                            </Tooltip>
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
                            <Tooltip content={
                                <div>
                                    <div className="font-semibold mb-1">Friend Activity - 40% Weight</div>
                                    <div className="text-xs opacity-90">
                                        Shows how your friends have engaged with this content:
                                        <ul className="list-disc ml-4 mt-1">
                                            <li><strong>Shared:</strong> +15 points - highest signal</li>
                                            <li><strong>Saved:</strong> +8 points - strong interest</li>
                                            <li><strong>Watched ≥10s:</strong> +5 points - genuine engagement</li>
                                            <li><strong>Mutual friends:</strong> +2 points each</li>
                                        </ul>
                                        This is the <strong>highest weighted factor</strong> because friend recommendations are highly trusted.
                                    </div>
                                </div>
                            }>
                                <Info className="w-4 h-4 text-gray-400 hover:text-indigo-600 transition" />
                            </Tooltip>
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
                                        {c.mutuals ? (
                                            `${c.mutuals} mutual friends interested`
                                        ) : c.venue_friends ? (
                                            `${c.venue_friends} friends love this place`
                                        ) : c.friend ? (
                                            <>
                                                {c.friend}{' '}
                                                {c.action === 'shared' && '📤 shared'}
                                                {c.action === 'saved' && '💾 saved'}
                                                {c.action === 'viewed' && '👀 watched ≥10s'}
                                            </>
                                        ) : (
                                            'Friend activity'
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
                            <Tooltip content={
                                <div>
                                    <div className="font-semibold mb-1">Proximity - 20% Weight</div>
                                    <div className="text-xs opacity-90">
                                        Considers how close this venue is to your current location:
                                        <ul className="list-disc ml-4 mt-1">
                                            <li>Closer venues score higher</li>
                                            <li>Walking distance matters for spontaneous visits</li>
                                            <li>Friend-recommended places get slightly larger radius</li>
                                        </ul>
                                        Balance between convenience and discovery.
                                    </div>
                                </div>
                            }>
                                <Info className="w-4 h-4 text-gray-400 hover:text-green-600 transition" />
                            </Tooltip>
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
                            <Tooltip content={
                                <div>
                                    <div className="font-semibold mb-1">Trending - 10% Weight</div>
                                    <div className="text-xs opacity-90">
                                        Measures how fresh and timely this content is:
                                        <ul className="list-disc ml-4 mt-1">
                                            <li><strong>Brand new</strong> (0-2 days): 100% score</li>
                                            <li><strong>This week</strong> (3-7 days): 70% score</li>
                                            <li><strong>Recent</strong> (8-14 days): 50% score</li>
                                            <li><strong>Older</strong> content scores lower</li>
                                        </ul>
                                        Keeps your feed fresh with new videos.
                                    </div>
                                </div>
                            }>
                                <Info className="w-4 h-4 text-gray-400 hover:text-orange-600 transition" />
                            </Tooltip>
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
