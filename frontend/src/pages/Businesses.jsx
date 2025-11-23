import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MapPin, Video, Eye, Bookmark, Share2, TrendingUp, Calendar, DollarSign, Tag, RefreshCw, Info } from 'lucide-react';

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
                <div className="absolute z-50 w-64 p-3 text-xs bg-gray-900 text-white rounded-lg shadow-lg bottom-full left-1/2 transform -translate-x-1/2 mb-2">
                    <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                    {content}
                </div>
            )}
        </div>
    );
}

export default function Businesses() {
    const [businesses, setBusinesses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [selectedBusiness, setSelectedBusiness] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchBusinesses();
    }, []);

    const fetchBusinesses = async (isRefresh = false) => {
        if (isRefresh) {
            setRefreshing(true);
        } else {
            setLoading(true);
        }
        try {
            const res = await axios.get('http://localhost:8000/businesses');
            setBusinesses(res.data.businesses);

            // Update selected business if it's being viewed
            if (selectedBusiness) {
                const updatedBusiness = res.data.businesses.find(b => b.venue_id === selectedBusiness.venue_id);
                if (updatedBusiness) {
                    setSelectedBusiness(updatedBusiness);
                }
            }
        } catch (e) {
            console.error('Failed to fetch businesses:', e);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const filteredBusinesses = businesses.filter(b =>
        (b.name && b.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (b.category && b.category.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (b.neighborhood && b.neighborhood.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    if (loading) {
        return <div className="h-full flex items-center justify-center bg-gray-50">
            <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                <p className="text-gray-500">Loading businesses...</p>
            </div>
        </div>;
    }

    return (
        <div className="h-full flex bg-gray-50">
            {/* Sidebar - Business List */}
            <div className="w-96 border-r border-gray-200 bg-white flex flex-col">
                <div className="p-6 border-b border-gray-200">
                    <div className="flex items-center justify-between mb-4">
                        <h1 className="text-2xl font-bold">Businesses</h1>
                        <button
                            onClick={() => fetchBusinesses(true)}
                            disabled={refreshing}
                            className="p-2 hover:bg-gray-100 rounded-lg transition disabled:opacity-50"
                            title="Refresh data"
                        >
                            <RefreshCw className={`w-5 h-5 text-gray-600 ${refreshing ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                    <input
                        type="text"
                        placeholder="Search businesses..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                        className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
                    />
                    <div className="mt-3 text-sm text-gray-500">
                        {filteredBusinesses.length} of {businesses.length} businesses
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {filteredBusinesses.map(business => (
                        <div
                            key={business.venue_id}
                            onClick={() => setSelectedBusiness(business)}
                            className={`p-4 border-b border-gray-100 cursor-pointer transition ${
                                selectedBusiness?.venue_id === business.venue_id
                                    ? 'bg-indigo-50 border-l-4 border-l-indigo-600'
                                    : 'hover:bg-gray-50'
                            }`}
                        >
                            <div className="font-semibold text-gray-900 mb-1">{business.name}</div>
                            <div className="text-xs text-gray-500 mb-2 flex items-center gap-1">
                                <MapPin className="w-3 h-3" />
                                {business.neighborhood || business.category}
                            </div>
                            <div className="flex items-center gap-3 text-xs">
                                <span className="flex items-center gap-1 text-indigo-600">
                                    <Video className="w-3 h-3" />
                                    {business.total_videos} videos
                                </span>
                                {business.price_tier && (
                                    <span className="px-2 py-0.5 bg-gray-100 rounded text-gray-600">
                                        {business.price_tier}
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Content - Business Details */}
            <div className="flex-1 overflow-y-auto">
                {selectedBusiness ? (
                    <div className="p-8">
                        {/* Business Header */}
                        <div className="bg-white rounded-2xl shadow-sm p-6 mb-6">
                            <h2 className="text-3xl font-bold text-gray-900 mb-2">{selectedBusiness.name}</h2>

                            <div className="flex flex-wrap gap-3 mb-4">
                                <div className="flex items-center gap-1 text-gray-600">
                                    <MapPin className="w-4 h-4" />
                                    <span className="text-sm">{selectedBusiness.neighborhood || 'NYC'}</span>
                                </div>
                                {selectedBusiness.category && (
                                    <div className="flex items-center gap-1 text-gray-600">
                                        <Tag className="w-4 h-4" />
                                        <span className="text-sm">{selectedBusiness.category}</span>
                                    </div>
                                )}
                                {selectedBusiness.price_tier && (
                                    <div className="flex items-center gap-1 text-gray-600">
                                        <DollarSign className="w-4 h-4" />
                                        <span className="text-sm">{selectedBusiness.price_tier}</span>
                                    </div>
                                )}
                                <div className="flex items-center gap-1 text-indigo-600 font-medium">
                                    <Video className="w-4 h-4" />
                                    <span className="text-sm">{selectedBusiness.total_videos} videos</span>
                                </div>
                            </div>

                            {selectedBusiness.description && (
                                <p className="text-gray-600 text-sm">{selectedBusiness.description}</p>
                            )}

                            {selectedBusiness.address && (
                                <div className="mt-4 text-xs text-gray-500">
                                    📍 {selectedBusiness.address}
                                </div>
                            )}
                        </div>

                        {/* Business Stats */}
                        {selectedBusiness.videos.length > 0 && (
                            <div className="grid grid-cols-4 gap-4 mb-6">
                                <StatCard
                                    icon={<Eye className="w-5 h-5" />}
                                    label="Total Views"
                                    value={selectedBusiness.videos.reduce((sum, v) => sum + v.engagement.total_views, 0)}
                                    color="blue"
                                />
                                <StatCard
                                    icon={<Bookmark className="w-5 h-5" />}
                                    label="Total Saves"
                                    value={selectedBusiness.videos.reduce((sum, v) => sum + v.engagement.saves, 0)}
                                    color="green"
                                />
                                <StatCard
                                    icon={<Share2 className="w-5 h-5" />}
                                    label="Total Shares"
                                    value={selectedBusiness.videos.reduce((sum, v) => sum + v.engagement.shares, 0)}
                                    color="purple"
                                />
                                <StatCard
                                    icon={<TrendingUp className="w-5 h-5" />}
                                    label="Quality Views"
                                    value={selectedBusiness.videos.reduce((sum, v) => sum + v.engagement.quality_views, 0)}
                                    color="orange"
                                    tooltip="Views where the user watched for 10+ seconds. These count toward social proof in the recommendation algorithm."
                                />
                            </div>
                        )}

                        {/* Videos List */}
                        <div className="bg-white rounded-2xl shadow-sm p-6">
                            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                                <Video className="w-5 h-5" />
                                Videos ({selectedBusiness.videos.length})
                            </h3>

                            {selectedBusiness.videos.length === 0 ? (
                                <div className="text-center py-12 text-gray-400 italic">
                                    No videos posted yet
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 gap-4">
                                    {selectedBusiness.videos.map(video => (
                                        <VideoCard key={video.id} video={video} />
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <div className="h-full flex items-center justify-center text-gray-400">
                        <div className="text-center">
                            <MapPin className="w-16 h-16 mx-auto mb-4 opacity-20" />
                            <p>Select a business to view details</p>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// Stat Card Component
function StatCard({ icon, label, value, color, tooltip }) {
    const colors = {
        blue: 'bg-blue-100 text-blue-600',
        green: 'bg-green-100 text-green-600',
        purple: 'bg-purple-100 text-purple-600',
        orange: 'bg-orange-100 text-orange-600'
    };

    return (
        <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-2 ${colors[color]}`}>
                {icon}
            </div>
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div className="flex items-center gap-1">
                <div className="text-xs text-gray-500">{label}</div>
                {tooltip && (
                    <Tooltip content={tooltip}>
                        <Info className="w-3 h-3 text-gray-400 hover:text-gray-600" />
                    </Tooltip>
                )}
            </div>
        </div>
    );
}

// Video Card Component
function VideoCard({ video }) {
    const getGradient = (categories) => {
        const gradients = {
            'cafe': 'from-purple-500 to-pink-500',
            'restaurant': 'from-orange-500 to-red-500',
            'bar': 'from-blue-500 to-cyan-500',
            'gallery': 'from-green-500 to-teal-500',
            'bakery': 'from-pink-500 to-yellow-500',
            'music': 'from-indigo-500 to-purple-500',
            'jazz': 'from-purple-500 to-indigo-500',
        };
        const category = categories?.[0]?.toLowerCase() || 'restaurant';
        return gradients[category] || gradients['restaurant'];
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Recently';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    };

    return (
        <div className="border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition">
            <div className={`h-32 bg-gradient-to-br ${getGradient(video.categories)} relative`}>
                <div className="absolute top-3 left-3">
                    <span className="px-3 py-1 bg-white/20 backdrop-blur text-white text-xs rounded-full font-medium">
                        {video.video_type || 'Video'}
                    </span>
                </div>
                <div className="absolute bottom-3 left-3 flex gap-1">
                    {video.categories?.slice(0, 3).map((cat, idx) => (
                        <span key={idx} className="px-2 py-0.5 bg-black/20 backdrop-blur text-white text-xs rounded">
                            {cat}
                        </span>
                    ))}
                </div>
            </div>

            <div className="p-4">
                <h4 className="font-semibold text-gray-900 mb-2">{video.title}</h4>
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">{video.description}</p>

                <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                    <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {formatDate(video.created_at)}
                    </div>
                    <div className="text-[10px] text-gray-400 font-mono">
                        {video.id}
                    </div>
                </div>

                {/* Engagement Stats */}
                <div className="grid grid-cols-4 gap-2">
                    <div className="flex flex-col items-center p-2 bg-blue-50 rounded-lg">
                        <Eye className="w-4 h-4 text-blue-600 mb-1" />
                        <span className="text-xs font-bold text-blue-900">{video.engagement.total_views}</span>
                        <span className="text-[10px] text-blue-600">views</span>
                    </div>
                    <div className="flex flex-col items-center p-2 bg-green-50 rounded-lg">
                        <Bookmark className="w-4 h-4 text-green-600 mb-1" />
                        <span className="text-xs font-bold text-green-900">{video.engagement.saves}</span>
                        <span className="text-[10px] text-green-600">saves</span>
                    </div>
                    <div className="flex flex-col items-center p-2 bg-purple-50 rounded-lg">
                        <Share2 className="w-4 h-4 text-purple-600 mb-1" />
                        <span className="text-xs font-bold text-purple-900">{video.engagement.shares}</span>
                        <span className="text-[10px] text-purple-600">shares</span>
                    </div>
                    <div className="flex flex-col items-center p-2 bg-orange-50 rounded-lg relative group">
                        <TrendingUp className="w-4 h-4 text-orange-600 mb-1" />
                        <span className="text-xs font-bold text-orange-900">{video.engagement.quality_views}</span>
                        <div className="flex items-center gap-0.5">
                            <span className="text-[10px] text-orange-600">quality</span>
                            <Tooltip content="Views ≥10 seconds. Counts toward social proof.">
                                <Info className="w-2.5 h-2.5 text-orange-400" />
                            </Tooltip>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
