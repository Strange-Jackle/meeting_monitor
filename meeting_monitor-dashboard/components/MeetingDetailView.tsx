import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    ArrowLeft,
    Clock,
    Calendar,
    Users,
    Star,
    Smile,
    MessageSquare,
    Award,
    BarChart3,
    FileText,
    Loader2,
    AlertCircle,
    Copy,
    CheckCircle
} from 'lucide-react';
import { getMeetingDetails, type MeetingDetails } from '../lib/api';
import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer
} from 'recharts';

const MeetingDetailView: React.FC = () => {
    const { meetingId } = useParams<{ meetingId: string }>();
    const navigate = useNavigate();
    const [meeting, setMeeting] = useState<MeetingDetails | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [copiedText, setCopiedText] = useState(false);
    const [activeTab, setActiveTab] = useState<'summary' | 'transcript' | 'battlecards' | 'entities'>('summary');

    useEffect(() => {
        async function fetchMeeting() {
            if (!meetingId) return;
            try {
                setLoading(true);
                const data = await getMeetingDetails(parseInt(meetingId));
                setMeeting(data);
                setError(null);
            } catch (err) {
                console.error('Failed to fetch meeting:', err);
                setError('Failed to load meeting details.');
            } finally {
                setLoading(false);
            }
        }
        fetchMeeting();
    }, [meetingId]);

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopiedText(true);
        setTimeout(() => setCopiedText(false), 2000);
    };

    const formatDate = (dateStr: string) => {
        try {
            const date = new Date(dateStr);
            return date.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateStr;
        }
    };

    const getSentimentColor = (score: number) => {
        if (score >= 70) return 'text-green-500';
        if (score >= 40) return 'text-yellow-500';
        return 'text-red-500';
    };

    const getSentimentLabel = (score: number) => {
        if (score >= 70) return 'Positive';
        if (score >= 40) return 'Neutral';
        return 'Negative';
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="animate-spin text-blue-500" size={40} />
            </div>
        );
    }

    if (error || !meeting) {
        return (
            <div className="flex flex-col items-center justify-center h-full gap-4">
                <AlertCircle className="text-red-500" size={48} />
                <h2 className="text-xl font-semibold text-gray-900">{error || 'Meeting not found'}</h2>
                <button
                    onClick={() => navigate('/dashboard/meetings')}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    Back to Meetings
                </button>
            </div>
        );
    }

    // Prepare radar data from engagement
    const radarData = meeting.engagement ? [
        { subject: 'Attention', A: meeting.engagement.attention || 0, fullMark: 100 },
        { subject: 'Interaction', A: meeting.engagement.interaction || 0, fullMark: 100 },
        { subject: 'Sentiment', A: meeting.engagement.sentiment || 0, fullMark: 100 },
        { subject: 'Speaking', A: meeting.engagement.speaking || 0, fullMark: 100 },
        { subject: 'Participation', A: meeting.engagement.participation || 0, fullMark: 100 },
        { subject: 'Clarity', A: meeting.engagement.clarity || 0, fullMark: 100 },
    ] : [];

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-6xl mx-auto space-y-6">
                {/* Back Button */}
                <button
                    onClick={() => navigate('/dashboard/meetings')}
                    className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
                >
                    <ArrowLeft size={20} />
                    <span>Back to Meetings</span>
                </button>

                {/* Header Card */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">{meeting.title}</h1>
                            <div className="flex flex-wrap items-center gap-4 mt-3 text-gray-500">
                                <span className="flex items-center gap-1">
                                    <Calendar size={16} />
                                    {formatDate(meeting.date)}
                                </span>
                                <span className="flex items-center gap-1">
                                    <Clock size={16} />
                                    {/* Duration would come from meeting data */}
                                    Session Complete
                                </span>
                                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${meeting.status === 'completed'
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-blue-50 text-blue-700'
                                    }`}>
                                    {meeting.status === 'completed' ? 'Analyzed' : meeting.status}
                                </span>
                            </div>
                        </div>

                        {/* Sentiment Score */}
                        <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 text-center min-w-[160px]">
                            <div className="flex items-center justify-center gap-2 mb-1">
                                <Smile className={getSentimentColor(meeting.sentiment_score || 0)} size={24} />
                                <span className={`text-3xl font-bold ${getSentimentColor(meeting.sentiment_score || 0)}`}>
                                    {meeting.sentiment_score || 0}
                                </span>
                            </div>
                            <p className="text-sm text-gray-600">Sentiment Score</p>
                            <p className={`text-xs font-medium ${getSentimentColor(meeting.sentiment_score || 0)}`}>
                                {getSentimentLabel(meeting.sentiment_score || 0)}
                            </p>
                        </div>
                    </div>

                    {/* Lead Info */}
                    {meeting.lead && (
                        <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-4">
                            {meeting.lead.name && (
                                <span className="flex items-center gap-2 text-sm text-gray-600">
                                    <Users size={16} />
                                    <strong>Contact:</strong> {meeting.lead.name}
                                </span>
                            )}
                            {meeting.lead.company && (
                                <span className="flex items-center gap-2 text-sm text-gray-600">
                                    <Award size={16} />
                                    <strong>Company:</strong> {meeting.lead.company}
                                </span>
                            )}
                        </div>
                    )}
                </div>

                {/* Tabs */}
                <div className="flex gap-2 border-b border-gray-200">
                    {(['summary', 'transcript', 'battlecards', 'entities'] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${activeTab === tab
                                    ? 'border-blue-600 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-900'
                                }`}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                            {tab === 'battlecards' && meeting.battlecards && (
                                <span className="ml-1.5 px-1.5 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                                    {meeting.battlecards.length}
                                </span>
                            )}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Main Content */}
                    <div className="lg:col-span-2">
                        {activeTab === 'summary' && (
                            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                        <FileText size={20} />
                                        Meeting Summary
                                    </h2>
                                    <button
                                        onClick={() => copyToClipboard(meeting.summary || '')}
                                        className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 transition-colors"
                                    >
                                        {copiedText ? <CheckCircle size={16} /> : <Copy size={16} />}
                                        {copiedText ? 'Copied!' : 'Copy'}
                                    </button>
                                </div>
                                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                    {meeting.summary || 'No summary available for this meeting.'}
                                </p>
                            </div>
                        )}

                        {activeTab === 'transcript' && (
                            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                                <div className="flex items-center justify-between mb-4">
                                    <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                        <MessageSquare size={20} />
                                        Full Transcript
                                    </h2>
                                    <button
                                        onClick={() => copyToClipboard(meeting.transcript || '')}
                                        className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-blue-600 transition-colors"
                                    >
                                        {copiedText ? <CheckCircle size={16} /> : <Copy size={16} />}
                                        {copiedText ? 'Copied!' : 'Copy'}
                                    </button>
                                </div>
                                <div className="max-h-[500px] overflow-y-auto">
                                    <p className="text-gray-700 leading-relaxed whitespace-pre-wrap font-mono text-sm">
                                        {meeting.transcript || 'No transcript available.'}
                                    </p>
                                </div>
                            </div>
                        )}

                        {activeTab === 'battlecards' && (
                            <div className="space-y-4">
                                {meeting.battlecards && meeting.battlecards.length > 0 ? (
                                    meeting.battlecards.map((bc, idx) => (
                                        <div key={idx} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                                            <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                                                <Award className="text-orange-500" size={20} />
                                                {bc.competitor}
                                            </h3>
                                            <ul className="space-y-2">
                                                {bc.counter_points?.map((point: string, i: number) => (
                                                    <li key={i} className="flex items-start gap-2 text-gray-700">
                                                        <span className="text-blue-500 mt-1">•</span>
                                                        <span>{point}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    ))
                                ) : (
                                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
                                        <Award className="mx-auto text-gray-300 mb-3" size={40} />
                                        <p className="text-gray-500">No battlecards generated for this meeting</p>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeTab === 'entities' && (
                            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                    <Star size={20} />
                                    Detected Entities
                                </h2>
                                {meeting.entities && meeting.entities.length > 0 ? (
                                    <div className="flex flex-wrap gap-2">
                                        {meeting.entities.map((entity: any, idx: number) => (
                                            <span
                                                key={idx}
                                                className={`px-3 py-1.5 rounded-full text-sm font-medium ${entity.label === 'person' ? 'bg-purple-100 text-purple-700' :
                                                        entity.label === 'organization' ? 'bg-blue-100 text-blue-700' :
                                                            entity.label === 'service' ? 'bg-green-100 text-green-700' :
                                                                'bg-gray-100 text-gray-700'
                                                    }`}
                                            >
                                                {entity.text}
                                                <span className="ml-1 text-xs opacity-70">({entity.label})</span>
                                            </span>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-gray-500 text-center py-4">No entities detected</p>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Sidebar - Engagement Radar */}
                    <div className="lg:col-span-1">
                        {meeting.engagement && radarData.length > 0 && (
                            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                    <BarChart3 size={20} />
                                    Engagement Metrics
                                </h3>
                                <ResponsiveContainer width="100%" height={250}>
                                    <RadarChart data={radarData}>
                                        <PolarGrid stroke="#e5e7eb" />
                                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 12 }} />
                                        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 10 }} />
                                        <Radar
                                            name="Engagement"
                                            dataKey="A"
                                            stroke="#3b82f6"
                                            fill="#3b82f6"
                                            fillOpacity={0.3}
                                        />
                                    </RadarChart>
                                </ResponsiveContainer>
                            </div>
                        )}

                        {/* Starred Hints */}
                        {meeting.starred_hints && meeting.starred_hints.length > 0 && (
                            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mt-6">
                                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                                    <Star className="text-yellow-500" size={20} />
                                    Starred Hints
                                </h3>
                                <ul className="space-y-2">
                                    {meeting.starred_hints.map((hint: any, idx: number) => (
                                        <li key={idx} className="text-sm text-gray-700 flex items-start gap-2">
                                            <Star size={14} className="text-yellow-500 mt-0.5" />
                                            {hint.hint_text}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MeetingDetailView;
