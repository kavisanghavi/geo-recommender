import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { ChevronUp, ChevronDown, Share2, Bookmark, Users, MapPin, TrendingUp, Target } from 'lucide-react';

export default function TikTokFeed({ userId }) {
    const [venues, setVenues] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [watchStartTime, setWatchStartTime] = useState(Date.now());
    const [loading, setLoading] = useState(true);
    const watchTimerRef = useRef(null);

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
        setWatchStartTime(Date.now());

        // Send watch time updates every 5 seconds
        watchTimerRef.current = setInterval(() => {
            const elapsed = Math.floor((Date.now() - watchStartTime) / 1000);
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
        const watchTime = Math.floor((Date.now() - watchStartTime) / 1000);

        // Log skip if less than 3 seconds
        if (watchTime < 3 && venues[currentIndex]) {
            logEngagement(venues[currentIndex].venue_id, watchTime, 'skip');
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
        const watchTime = Math.floor((Date.now() - watchStartTime) / 1000);
        const venue = venues[currentIndex];

        await logEngagement(venue.venue_id, watchTime, 'save');
        alert('Saved! ✓');
    };

    const handleShare = async () => {
        const watchTime = Math.floor((Date.now() - watchStartTime) / 1000);
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

    return (
        <div className="h-screen overflow-hidden bg-black relative">
            {/* Video/Image Container */}
            <div className="h-full w-full relative">
                {/* Background Image (simulating video) */}
                <img
                    src={currentVenue.video_url || `https://source.unsplash.com/random/1080x1920/?${currentVenue.categories[0]}`}
                    alt={currentVenue.name}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                        e.target.src = 'https://source.unsplash.com/random/1080x1920/?restaurant';
                    }}
                />

                {/* Gradient Overlays */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30" />

                {/* Top Info Bar */}
                <div className="absolute top-0 left-0 right-0 p-4 flex justify-between items-start z-20">
                    <div className="text-white">
                        <div className="text-xs opacity-75">{currentIndex + 1} / {venues.length}</div>
                    </div>
                    <div className="flex gap-2">
                        <span className="px-3 py-1 bg-white/20 backdrop-blur rounded-full text-white text-xs font-bold">
                            {currentVenue.neighborhood}
                        </span>
                        <span className="px-3 py-1 bg-white/20 backdrop-blur rounded-full text-white text-xs">
                            {'$'.repeat(currentVenue.price_tier)}
                        </span>
                    </div>
                </div>

                {/* Venue Info (Bottom) */}
                <div className="absolute bottom-0 left-0 right-0 p-6 text-white z-20">
                    <h1 className="text-3xl font-bold mb-2">{currentVenue.name}</h1>
                    <p className="text-sm opacity-90 mb-3 line-clamp-2">{currentVenue.description}</p>

                    {/* Categories */}
                    <div className="flex gap-2 mb-4">
                        {currentVenue.categories.slice(0, 3).map((cat, idx) => (
                            <span key={idx} className="px-2 py-1 bg-white/10 backdrop-blur rounded text-xs">
                                {cat}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Right Action Buttons */}
                <div className="absolute right-4 bottom-32 flex flex-col gap-6 z-20">
                    <button
                        onClick={handleSave}
                        className="flex flex-col items-center text-white"
                    >
                        <div className="w-14 h-14 rounded-full bg-white/20 backdrop-blur flex items-center justify-center mb-1 hover:bg-white/30 transition">
                            <Bookmark className="w-6 h-6" />
                        </div>
                        <span className="text-xs">Save</span>
                    </button>

                    <button
                        onClick={handleShare}
                        className="flex flex-col items-center text-white"
                    >
                        <div className="w-14 h-14 rounded-full bg-white/20 backdrop-blur flex items-center justify-center mb-1 hover:bg-white/30 transition">
                            <Share2 className="w-6 h-6" />
                        </div>
                        <span className="text-xs">Share</span>
                    </button>
                </div>

                {/* Swipe Navigation */}
                <div className="absolute right-1/2 translate-x-1/2 bottom-8 flex flex-col gap-3 z-20">
                    <button
                        onClick={handleSwipePrevious}
                        disabled={currentIndex === 0}
                        className="w-12 h-12 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-white disabled:opacity-30"
                    >
                        <ChevronUp className="w-6 h-6" />
                    </button>
                    <button
                        onClick={handleSwipeNext}
                        className="w-12 h-12 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-white"
                    >
                        <ChevronDown className="w-6 h-6" />
                    </button>
                </div>

                {/* Explanation Panel */}
                <ExplanationPanel explanation={currentVenue.explanation} />
            </div>
        </div>
    );
}

// Explanation Panel Component
function ExplanationPanel({ explanation }) {
    const [expanded, setExpanded] = useState(false);

    if (!explanation) return null;

    return (
        <div className="absolute bottom-20 left-0 right-0 z-30">
            {/* Collapsed State */}
            {!expanded && (
                <button
                    onClick={() => setExpanded(true)}
                    className="w-full bg-black/60 backdrop-blur-xl text-white p-4 text-left border-t border-white/10"
                >
                    <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold">🎯 Why this venue?</span>
                        <ChevronUp className="w-5 h-5" />
                    </div>
                    <div className="flex gap-2 flex-wrap">
                        {explanation.social_proof.contributors.length > 0 && (
                            <span className="px-2 py-1 bg-indigo-500/30 rounded text-xs">
                                👥 {explanation.social_proof.contributors.length} friends
                            </span>
                        )}
                        {explanation.proximity.distance_km < 1 && (
                            <span className="px-2 py-1 bg-green-500/30 rounded text-xs">
                                📍 {explanation.proximity.distance_km}km away
                            </span>
                        )}
                        {explanation.trending.recent_count > 5 && (
                            <span className="px-2 py-1 bg-orange-500/30 rounded text-xs">
                                🔥 Trending
                            </span>
                        )}
                    </div>
                </button>
            )}

            {/* Expanded State */}
            {expanded && (
                <div className="bg-black/80 backdrop-blur-xl text-white p-6 max-h-[60vh] overflow-y-auto border-t border-white/10">
                    <button
                        onClick={() => setExpanded(false)}
                        className="flex items-center justify-between w-full mb-4"
                    >
                        <span className="font-bold text-lg">Algorithm Breakdown</span>
                        <ChevronDown className="w-5 h-5" />
                    </button>

                    <div className="space-y-4">
                        {/* Taste Match */}
                        <ScoreSection
                            icon={<Target className="w-5 h-5" />}
                            label="Taste Match"
                            score={explanation.taste_match.score}
                            reason={explanation.taste_match.reason}
                            color="bg-blue-500"
                        />

                        {/* Social Proof */}
                        <ScoreSection
                            icon={<Users className="w-5 h-5" />}
                            label="Friend Activity"
                            score={explanation.social_proof.score}
                            reason={explanation.social_proof.reason}
                            color="bg-indigo-500"
                        >
                            {explanation.social_proof.contributors.length > 0 && (
                                <ul className="mt-2 space-y-1 text-sm">
                                    {explanation.social_proof.contributors.map((c, idx) => (
                                        <li key={idx} className="flex justify-between items-center opacity-90">
                                            <span>
                                                {c.friend || `${c.mutuals} mutuals`}{' '}
                                                {c.action === 'shared' && '📤'}
                                                {c.action === 'saved' && '💾'}
                                                {c.action === 'viewed' && '👀'}
                                            </span>
                                            <span className="text-xs text-green-400">+{c.boost} pts</span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </ScoreSection>

                        {/* Proximity */}
                        <ScoreSection
                            icon={<MapPin className="w-5 h-5" />}
                            label="Proximity"
                            score={explanation.proximity.score}
                            reason={explanation.proximity.reason}
                            color="bg-green-500"
                        />

                        {/* Trending */}
                        <ScoreSection
                            icon={<TrendingUp className="w-5 h-5" />}
                            label="Trending"
                            score={explanation.trending.score}
                            reason={explanation.trending.reason}
                            color="bg-orange-500"
                        />
                    </div>
                </div>
            )}
        </div>
    );
}

// Score Section Component
function ScoreSection({ icon, label, score, reason, color, children }) {
    return (
        <div className="border-l-4 pl-3" style={{ borderColor: color.replace('bg-', '') }}>
            <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2 font-semibold">
                    {icon}
                    <span>{label}</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-white/10 rounded-full overflow-hidden">
                        <div
                            className={`h-full ${color}`}
                            style={{ width: `${score * 100}%` }}
                        />
                    </div>
                    <span className="text-sm w-12 text-right">{Math.round(score * 100)}%</span>
                </div>
            </div>
            <p className="text-sm opacity-75">{reason}</p>
            {children}
        </div>
    );
}
