import React from 'react';
import {
    Clipboard,
    AlertOctagon,
    Heart,
    Search,
    ChevronDown,
    Settings,
    MessageSquare,
    Video,
    Calendar,
    MoreVertical,
    CheckCircle2
} from 'lucide-react';
import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer
} from 'recharts';

const OverviewView: React.FC = () => {
    const radarData = [
        { subject: 'Attention', A: 120, fullMark: 150 },
        { subject: 'Interaction', A: 98, fullMark: 150 },
        { subject: 'Sentiment', A: 86, fullMark: 150 },
        { subject: 'Speaking', A: 99, fullMark: 150 },
        { subject: 'Participation', A: 85, fullMark: 150 },
        { subject: 'Clarity', A: 65, fullMark: 150 },
    ];

    const meetings = [
        { title: 'Sales Call - TechCorp', date: 'Yesterday, 2:00 PM', type: 'Zoom', status: 'Analyzed' },
        { title: 'Team Standup', date: 'Oct 25, 10:30 AM', type: 'Google Meet', status: 'Completed' },
        { title: 'Client Presentation', date: 'Oct 24, 11:00 AM', type: 'Microsoft Teams', status: 'Analyzed' },
        { title: 'Product Demo Call', date: 'Oct 24, 02:00 PM', type: 'Zoom', status: 'Analyzed' },
        { title: 'Customer Discovery', date: 'Oct 23, 03:30 PM', type: 'Google Meet', status: 'Completed' },
    ];

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Hi Guest!</h1>
                        <p className="text-gray-500 mt-1">You have 2 new messages and 15 new tasks.</p>
                    </div>
                    <div className="flex items-center gap-3">
                        <button className="flex items-center gap-2 px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 transition-colors font-medium text-sm">
                            <MessageSquare size={16} />
                            Messages
                        </button>
                        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm">
                            <Settings size={16} />
                            Settings
                        </button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="border-b border-gray-200">
                    <nav className="flex items-center gap-8">
                        <button className="py-3 border-b-2 border-blue-600 text-blue-600 font-medium text-sm">
                            Overview
                        </button>
                        <button className="py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium text-sm">
                            Insights
                        </button>
                        <button className="py-3 border-b-2 border-transparent text-gray-500 hover:text-gray-700 font-medium text-sm">
                            Participants
                        </button>
                    </nav>
                </div>

                {/* Metric Cards Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {/* Card 1 */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between h-48">
                        <div>
                            <div className="flex justify-between items-start mb-4">
                                <span className="font-semibold text-gray-900">12 Meetings Analyzed</span>
                                <button className="flex items-center gap-1 text-xs font-medium text-gray-500 bg-gray-50 px-2 py-1 rounded border border-gray-200">
                                    Today <ChevronDown size={12} />
                                </button>
                            </div>
                            <div className="mb-4">
                                <Search className="text-blue-500 bg-blue-50 p-1.5 rounded-lg w-8 h-8" />
                            </div>
                        </div>
                        <div className="text-sm font-medium text-gray-500">
                            AI Insights Generated: <span className="text-gray-900 font-bold">38</span>
                        </div>
                    </div>

                    {/* Card 2 */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between h-48">
                        <div className="flex justify-between items-start">
                            <div className="font-semibold text-gray-900">Action Items</div>
                            <Clipboard className="text-gray-400" size={18} />
                        </div>
                        <div>
                            <div className="text-4xl font-bold text-gray-900 mb-1">7</div>
                            <div className="text-sm text-gray-500">Pending Actions</div>
                        </div>
                        <div className="text-sm font-medium text-gray-500">
                            Completed Today: <span className="text-gray-900 font-bold">5</span>
                        </div>
                    </div>

                    {/* Card 3 */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between h-48">
                        <div className="flex justify-between items-start">
                            <div className="font-semibold text-gray-900">AI Quality Alerts</div>
                            <AlertOctagon className="text-red-400" size={18} />
                        </div>
                        <div>
                            <div className="text-4xl font-bold text-gray-900 mb-1">3</div>
                            <div className="text-sm text-gray-500">Audio Issues</div>
                        </div>
                        <div className="text-sm font-medium text-gray-500">
                            Resolved Today: <span className="text-gray-900 font-bold">2</span>
                        </div>
                    </div>

                    {/* Card 4 */}
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between h-48">
                        <div className="flex justify-between items-start">
                            <div className="font-semibold text-gray-900">AI Sentiment Score</div>
                            <Heart className="text-green-500" size={18} />
                        </div>
                        <div>
                            <div className="text-4xl font-bold text-gray-900 mb-1">87</div>
                            <div className="text-sm text-gray-500">Avg. Positivity</div>
                        </div>
                        <div className="text-sm font-medium text-gray-500">
                            Engagement Score: <span className="text-gray-900 font-bold">92</span>
                        </div>
                    </div>
                </div>

                {/* Charts & History Section */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                    {/* Engagement Radar Chart */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-lg font-bold text-gray-900">Participant Engagement</h2>
                            <div className="flex bg-gray-100 rounded-lg p-1">
                                <button className="px-3 py-1 text-xs font-semibold bg-white shadow-sm rounded-md text-gray-900">This Week</button>
                                <button className="px-3 py-1 text-xs font-semibold text-gray-500">Last Week</button>
                            </div>
                        </div>

                        <div className="flex-1 flex flex-col items-center justify-center min-h-[300px]">
                            <ResponsiveContainer width="100%" height={300}>
                                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                                    <PolarGrid stroke="#e5e7eb" />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#6b7280', fontSize: 12 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 150]} tick={false} axisLine={false} />
                                    <Radar
                                        name="Engagement"
                                        dataKey="A"
                                        stroke="#3b82f6"
                                        strokeWidth={2}
                                        fill="#3b82f6"
                                        fillOpacity={0.5}
                                    />
                                </RadarChart>
                            </ResponsiveContainer>

                            <div className="flex items-center gap-4 mt-4 text-xs text-gray-500">
                                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500"></span> High Engagement</div>
                                <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-300"></span> Medium Engagement</div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 mt-6 pt-6 border-t border-gray-50">
                            <div className="text-center">
                                <div className="text-3xl font-bold text-gray-900">47</div>
                                <div className="text-xs text-gray-500">Active Participants</div>
                            </div>
                            <div className="text-center">
                                <div className="text-3xl font-bold text-gray-900">35<span className="text-sm font-normal text-gray-400">m</span></div>
                                <div className="text-xs text-gray-500">Avg. Speaking Time</div>
                            </div>
                        </div>
                    </div>

                    {/* Meeting History List */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 flex flex-col">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-lg font-bold text-gray-900">Recent Meetings</h2>
                            <div className="flex bg-gray-100 rounded-lg p-1">
                                <button className="px-3 py-1 text-xs font-semibold bg-white shadow-sm rounded-md text-gray-900">History</button>
                                <button className="px-3 py-1 text-xs font-semibold text-gray-500">Upcoming</button>
                            </div>
                        </div>

                        <div className="flex-1 overflow-auto space-y-4">
                            {meetings.map((meeting, index) => (
                                <div key={index} className="flex items-center justify-between p-4 hover:bg-gray-50 rounded-xl transition-colors border border-transparent hover:border-gray-100 group cursor-pointer">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-sm ${meeting.type === 'Zoom' ? 'bg-blue-100 text-blue-600' : 'bg-indigo-100 text-indigo-600'}`}>
                                            <Video size={20} />
                                        </div>
                                        <div>
                                            <div className="font-bold text-gray-900 group-hover:text-blue-600 transition-colors">{meeting.title}</div>
                                            <div className="text-xs text-gray-500 flex items-center gap-1.5 mt-0.5">
                                                <Calendar size={12} /> {meeting.date}
                                            </div>
                                        </div>
                                    </div>
                                    <div className={`px-3 py-1 rounded-full text-xs font-bold ${meeting.status === 'Analyzed'
                                        ? 'bg-green-100 text-green-700'
                                        : 'bg-blue-50 text-blue-700'
                                        }`}>
                                        {meeting.status}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};

export default OverviewView;
