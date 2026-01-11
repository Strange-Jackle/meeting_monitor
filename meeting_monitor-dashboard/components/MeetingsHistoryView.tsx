import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Video,
    Calendar,
    Search,
    Filter,
    ChevronRight,
    Clock,
    Users,
    BarChart3,
    Loader2,
    AlertCircle
} from 'lucide-react';
import { getMeetings, type Meeting } from '../lib/api';

const MeetingsHistoryView: React.FC = () => {
    const navigate = useNavigate();
    const [meetings, setMeetings] = useState<Meeting[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [filter, setFilter] = useState<'all' | 'analyzed' | 'pending'>('all');

    useEffect(() => {
        async function fetchMeetings() {
            try {
                setLoading(true);
                const response = await getMeetings(50);
                setMeetings(response.meetings || []);
                setError(null);
            } catch (err) {
                console.error('Failed to fetch meetings:', err);
                setError('Failed to load meetings. Is the backend running?');
            } finally {
                setLoading(false);
            }
        }
        fetchMeetings();
    }, []);

    const filteredMeetings = meetings.filter(m => {
        const matchesSearch = m.title.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesFilter = filter === 'all' ||
            (filter === 'analyzed' && m.status === 'Analyzed') ||
            (filter === 'pending' && m.status !== 'Analyzed');
        return matchesSearch && matchesFilter;
    });

    const formatDate = (dateStr: string) => {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateStr;
        }
    };

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-6xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Meeting History</h1>
                        <p className="text-gray-500 mt-1">
                            View all your past meetings and their AI analysis
                        </p>
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="text-sm text-gray-500">
                            {meetings.length} meetings total
                        </span>
                    </div>
                </div>

                {/* Search and Filter */}
                <div className="flex flex-col sm:flex-row gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        <input
                            type="text"
                            placeholder="Search meetings..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                        />
                    </div>
                    <div className="flex gap-2">
                        {(['all', 'analyzed', 'pending'] as const).map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === f
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
                                    }`}
                            >
                                {f.charAt(0).toUpperCase() + f.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Error Banner */}
                {error && (
                    <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg flex items-center gap-2">
                        <AlertCircle size={18} />
                        <span className="text-sm">{error}</span>
                    </div>
                )}

                {/* Meetings List */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100">
                    {loading ? (
                        <div className="flex items-center justify-center py-16">
                            <Loader2 className="animate-spin text-blue-500" size={32} />
                        </div>
                    ) : filteredMeetings.length === 0 ? (
                        <div className="text-center py-16">
                            <Video className="mx-auto text-gray-300 mb-4" size={48} />
                            <h3 className="text-lg font-medium text-gray-900 mb-1">No meetings found</h3>
                            <p className="text-gray-500">
                                {searchQuery ? 'Try a different search term' : 'Start a session to see meetings here'}
                            </p>
                        </div>
                    ) : (
                        <div className="divide-y divide-gray-100">
                            {filteredMeetings.map((meeting) => (
                                <div
                                    key={meeting.id}
                                    onClick={() => navigate(`/dashboard/meetings/${meeting.id}`)}
                                    className="flex items-center justify-between p-5 hover:bg-gray-50 transition-colors cursor-pointer group"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${meeting.status === 'Analyzed'
                                                ? 'bg-green-100 text-green-600'
                                                : 'bg-blue-100 text-blue-600'
                                            }`}>
                                            <Video size={22} />
                                        </div>
                                        <div>
                                            <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                                                {meeting.title}
                                            </h3>
                                            <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                                                <span className="flex items-center gap-1">
                                                    <Calendar size={14} />
                                                    {formatDate(meeting.date)}
                                                </span>
                                                <span className="flex items-center gap-1">
                                                    <Clock size={14} />
                                                    {Math.round((meeting.duration || 0) / 60)}m
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${meeting.status === 'Analyzed'
                                                ? 'bg-green-100 text-green-700'
                                                : 'bg-blue-50 text-blue-700'
                                            }`}>
                                            {meeting.status}
                                        </span>
                                        <ChevronRight className="text-gray-400 group-hover:text-blue-500 transition-colors" size={20} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MeetingsHistoryView;
