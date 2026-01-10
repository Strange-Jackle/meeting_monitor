import React, { useState } from 'react';
import { Play, User, Building2, Phone, Link as LinkIcon, AlertCircle } from 'lucide-react';

const MeetingIntelligenceView: React.FC = () => {
    const [meetingUrl, Hb] = useState('');
    const [formData, setFormData] = useState({
        customerName: '',
        customerContact: '',
        companyName: ''
    });

    const handleStartMeeting = () => {
        if (meetingUrl) {
            window.open(meetingUrl, '_blank');
        }
    };

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Meeting Intelligence</h1>
                        <p className="text-gray-500 mt-1">Configure user details and launch your monitored meeting.</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Customer Information Card */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="flex items-center gap-2 mb-6 text-lg font-semibold text-gray-900 border-b border-gray-100 pb-4">
                            <User className="text-blue-600" size={20} />
                            <h2>Customer Information</h2>
                        </div>

                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label htmlFor="customerName" className="text-sm font-medium text-gray-700 block">Customer Name</label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                                    <input
                                        type="text"
                                        id="customerName"
                                        value={formData.customerName}
                                        onChange={(e) => setFormData({ ...formData, customerName: e.target.value })}
                                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder:text-gray-400"
                                        placeholder="e.g. John Doe"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label htmlFor="customerContact" className="text-sm font-medium text-gray-700 block">Customer Contact</label>
                                <div className="relative">
                                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                                    <input
                                        type="text"
                                        id="customerContact"
                                        value={formData.customerContact}
                                        onChange={(e) => setFormData({ ...formData, customerContact: e.target.value })}
                                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder:text-gray-400"
                                        placeholder="e.g. +1 (555) 000-0000"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label htmlFor="companyName" className="text-sm font-medium text-gray-700 block">Company Name</label>
                                <div className="relative">
                                    <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                                    <input
                                        type="text"
                                        id="companyName"
                                        value={formData.companyName}
                                        onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder:text-gray-400"
                                        placeholder="e.g. Acme Corp"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Meeting Launcher Card */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 h-fit">
                        <div className="flex items-center gap-2 mb-6 text-lg font-semibold text-gray-900 border-b border-gray-100 pb-4">
                            <LinkIcon className="text-blue-600" size={20} />
                            <h2>Launch Meeting</h2>
                        </div>

                        <div className="space-y-6">
                            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 flex items-start gap-3">
                                <AlertCircle className="text-blue-600 shrink-0 mt-0.5" size={18} />
                                <p className="text-sm text-blue-800">
                                    Paste your meeting link below. A new window will open for the meeting, and our intelligence system will start monitoring in the background.
                                </p>
                            </div>

                            <div className="space-y-2">
                                <label htmlFor="meetingUrl" className="text-sm font-medium text-gray-700 block">Meeting URL</label>
                                <input
                                    type="url"
                                    id="meetingUrl"
                                    value={meetingUrl}
                                    onChange={(e) => Hb(e.target.value)}
                                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all placeholder:text-gray-400 mb-2"
                                    placeholder="https://meet.google.com/..."
                                />
                            </div>

                            <button
                                onClick={handleStartMeeting}
                                disabled={!meetingUrl}
                                className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-white font-medium transition-all shadow-lg hover:shadow-blue-500/25 ${meetingUrl
                                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 cursor-pointer transform hover:-translate-y-0.5'
                                    : 'bg-gray-300 cursor-not-allowed'
                                    }`}
                            >
                                <Play size={20} fill="currentColor" />
                                Start Meeting Intelligence
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MeetingIntelligenceView;
