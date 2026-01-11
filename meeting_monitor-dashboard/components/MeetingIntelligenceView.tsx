import React, { useState, useEffect, useRef } from 'react';
import { Play, User, Building2, Phone, Link as LinkIcon, AlertCircle, Loader2, CheckCircle, Upload, FileText, Trash2, X, Eye } from 'lucide-react';
import { startSession, stopSession, uploadDocument, getDocuments, deleteDocument, analyzeDocument, type Document, type DocumentAnalysis } from '../lib/api';

const MeetingIntelligenceView: React.FC = () => {
    const [meetingUrl, setMeetingUrl] = useState('');
    const [formData, setFormData] = useState({
        customerName: '',
        customerContact: '',
        companyName: ''
    });
    const [isStarting, setIsStarting] = useState(false);
    const [sessionActive, setSessionActive] = useState(false);
    const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

    // Document upload state
    const [documents, setDocuments] = useState<Document[]>([]);
    const [uploading, setUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const [analyzingId, setAnalyzingId] = useState<number | null>(null);
    const [analysisResult, setAnalysisResult] = useState<{ filename: string; analysis: DocumentAnalysis } | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        fetchDocuments();
    }, []);

    const fetchDocuments = async () => {
        try {
            const result = await getDocuments();
            setDocuments(result.documents || []);
        } catch (error) {
            console.error('Failed to fetch documents:', error);
        }
    };

    const handleFileUpload = async (files: FileList | null) => {
        if (!files || files.length === 0) return;

        setUploading(true);

        for (const file of Array.from(files)) {
            try {
                await uploadDocument(file);
                setStatusMessage({ type: 'success', text: `Uploaded: ${file.name}` });
            } catch (error: any) {
                setStatusMessage({ type: 'error', text: error.message || 'Upload failed' });
            }
        }

        setUploading(false);
        fetchDocuments();
    };

    const handleDeleteDocument = async (docId: number) => {
        try {
            await deleteDocument(docId);
            setDocuments(docs => docs.filter(d => d.id !== docId));
        } catch (error) {
            console.error('Delete failed:', error);
        }
    };

    const handleAnalyzeDocument = async (docId: number) => {
        setAnalyzingId(docId);
        setStatusMessage({ type: 'info', text: 'Analyzing document with AI...' });

        try {
            const result = await analyzeDocument(docId);
            setAnalysisResult({ filename: result.filename, analysis: result.analysis });
            setStatusMessage({ type: 'success', text: 'Analysis complete!' });
        } catch (error: any) {
            setStatusMessage({ type: 'error', text: error.message || 'Analysis failed' });
        } finally {
            setAnalyzingId(null);
        }
    };

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        handleFileUpload(e.dataTransfer.files);
    };

    const formatFileSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const getFileIcon = (type: string) => {
        switch (type) {
            case 'pdf': return '📄';
            case 'pptx': return '📊';
            case 'docx': return '📝';
            default: return '📁';
        }
    };

    const handleStartMeeting = async () => {
        if (!meetingUrl) return;

        setIsStarting(true);
        setStatusMessage({ type: 'info', text: 'Starting meeting intelligence...' });

        try {
            // Start session - this will trigger remote overlay on teammate's machine
            const sessionResult = await startSession({ capture_mode: 'remote' });
            console.log('Session started:', sessionResult);

            setSessionActive(true);
            setStatusMessage({ type: 'success', text: '✓ Intelligence active! Remote overlay launched.' });

            if (meetingUrl) {
                window.open(meetingUrl, '_blank');
            }
        } catch (error) {
            console.error('Failed to start session:', error);
            setStatusMessage({ type: 'error', text: 'Failed to start. Is the backend running?' });
        } finally {
            setIsStarting(false);
        }
    };

    const handleStopSession = async () => {
        try {
            await stopSession();
            setSessionActive(false);
            setStatusMessage({ type: 'info', text: 'Session stopped successfully.' });
        } catch (error) {
            console.error('Failed to stop session:', error);
        }
    };

    return (
        <div className="h-full overflow-y-auto p-6">
            <div className="max-w-5xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Meeting Intelligence</h1>
                        <p className="text-gray-500 mt-1">Start AI-powered meeting assistance</p>
                    </div>
                    {sessionActive && (
                        <button
                            onClick={handleStopSession}
                            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center gap-2"
                        >
                            <X size={18} />
                            Stop Session
                        </button>
                    )}
                </div>

                {/* Status Message */}
                {statusMessage && (
                    <div className={`flex items-center gap-3 px-4 py-3 rounded-lg ${statusMessage.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' :
                        statusMessage.type === 'error' ? 'bg-red-50 text-red-800 border border-red-200' :
                            'bg-blue-50 text-blue-800 border border-blue-200'
                        }`}>
                        {statusMessage.type === 'success' ? <CheckCircle size={18} /> :
                            statusMessage.type === 'error' ? <AlertCircle size={18} /> :
                                <Loader2 size={18} className="animate-spin" />}
                        <span className="text-sm font-medium">{statusMessage.text}</span>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Left Column - Meeting Setup */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">

                        {/* Customer Info - NOW AT TOP */}
                        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <User size={20} />
                            Customer Details
                        </h2>
                        <div className="space-y-3 mb-6">
                            <div className="relative">
                                <User size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Customer Name"
                                    value={formData.customerName}
                                    onChange={(e) => setFormData({ ...formData, customerName: e.target.value })}
                                    className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                />
                            </div>
                            <div className="relative">
                                <Building2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="Company Name"
                                    value={formData.companyName}
                                    onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                                    className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                                />
                            </div>
                        </div>

                        {/* Meeting Link Section */}
                        <div className="pt-6 border-t border-gray-100">
                            <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                                <LinkIcon size={16} />
                                Meeting Link
                            </h3>

                            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-lg p-3 mb-4">
                                <p className="text-xs text-blue-800">
                                    Paste your meeting link. The overlay will appear for real-time AI assistance.
                                </p>
                            </div>

                            <input
                                type="url"
                                value={meetingUrl}
                                onChange={(e) => setMeetingUrl(e.target.value)}
                                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all mb-4"
                                placeholder="https://meet.google.com/..."
                                disabled={sessionActive}
                            />

                            <button
                                onClick={handleStartMeeting}
                                disabled={!meetingUrl || isStarting || sessionActive}
                                className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg text-white font-medium transition-all ${meetingUrl && !isStarting && !sessionActive
                                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-blue-500/25'
                                    : 'bg-gray-300 cursor-not-allowed'
                                    }`}
                            >
                                {isStarting ? (
                                    <Loader2 className="animate-spin" size={20} />
                                ) : (
                                    <Play size={20} fill="currentColor" />
                                )}
                                {sessionActive ? 'Session Active' : 'Start Meeting Intelligence'}
                            </button>
                        </div>
                    </div>

                    {/* Right Column - Document Upload */}
                    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                        <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                            <FileText size={20} />
                            Meeting Documents
                        </h2>

                        {/* Upload Area */}
                        <div
                            onDragEnter={handleDrag}
                            onDragLeave={handleDrag}
                            onDragOver={handleDrag}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                            className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${dragActive
                                ? 'border-blue-500 bg-blue-50'
                                : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                                }`}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                multiple
                                accept=".pdf,.pptx,.docx"
                                onChange={(e) => handleFileUpload(e.target.files)}
                                className="hidden"
                            />

                            {uploading ? (
                                <Loader2 className="mx-auto animate-spin text-blue-500 mb-2" size={32} />
                            ) : (
                                <Upload className="mx-auto text-gray-400 mb-2" size={32} />
                            )}
                            <p className="text-sm font-medium text-gray-700">
                                {uploading ? 'Uploading...' : 'Drop files here or click to upload'}
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                                PDF, PPTX, DOCX (max 10MB)
                            </p>
                        </div>

                        {/* Document List */}
                        <div className="mt-4 space-y-3 max-h-72 overflow-y-auto">
                            {documents.length === 0 ? (
                                <p className="text-sm text-gray-500 text-center py-4">
                                    No documents uploaded yet
                                </p>
                            ) : (
                                documents.map((doc) => (
                                    <div
                                        key={doc.id}
                                        className="p-4 bg-gradient-to-r from-gray-50 to-white rounded-xl border border-gray-100 hover:border-blue-200 hover:shadow-md transition-all"
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-xl flex items-center justify-center text-2xl shadow-sm">
                                                    {getFileIcon(doc.file_type)}
                                                </div>
                                                <div>
                                                    <p className="text-sm font-semibold text-gray-900">
                                                        {doc.filename}
                                                    </p>
                                                    <p className="text-xs text-gray-500 mt-0.5">
                                                        {formatFileSize(doc.file_size)} • {doc.file_type.toUpperCase()}
                                                    </p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleDeleteDocument(doc.id);
                                                }}
                                                className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </div>

                                        {/* Analyze Button - Always visible */}
                                        <button
                                            onClick={() => handleAnalyzeDocument(doc.id)}
                                            disabled={analyzingId === doc.id}
                                            className={`mt-3 w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${analyzingId === doc.id
                                                ? 'bg-blue-100 text-blue-600 cursor-wait'
                                                : 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white hover:from-blue-600 hover:to-indigo-600 shadow-sm hover:shadow-md'
                                                }`}
                                        >
                                            {analyzingId === doc.id ? (
                                                <>
                                                    <Loader2 size={16} className="animate-spin" />
                                                    Analyzing with AI...
                                                </>
                                            ) : (
                                                <>
                                                    <Eye size={16} />
                                                    Analyze Document
                                                </>
                                            )}
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Enhanced Analysis Results Modal */}
            {analysisResult && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[85vh] overflow-hidden animate-in fade-in zoom-in-95">
                        {/* Modal Header */}
                        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-5 text-white">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                                        <FileText size={20} />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold">AI Document Analysis</h3>
                                        <p className="text-sm text-blue-100 mt-0.5">{analysisResult.filename}</p>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setAnalysisResult(null)}
                                    className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                                >
                                    <X size={20} />
                                </button>
                            </div>

                            {/* Stats Bar */}
                            <div className="flex gap-4 mt-4 text-sm">
                                <div className="bg-white/10 px-3 py-1.5 rounded-lg">
                                    📄 {analysisResult.analysis.file_type?.toUpperCase() || 'Document'}
                                </div>
                                <div className="bg-white/10 px-3 py-1.5 rounded-lg">
                                    📊 {analysisResult.analysis.pages_analyzed || analysisResult.analysis.slides_analyzed || analysisResult.analysis.paragraphs_analyzed || 0} items analyzed
                                </div>
                            </div>
                        </div>

                        {/* Modal Content */}
                        <div className="p-6 overflow-y-auto max-h-[55vh] space-y-6">
                            {/* Key AI Insights Section */}
                            {analysisResult.analysis.key_insights && analysisResult.analysis.key_insights.length > 0 && (
                                <div className="bg-gradient-to-br from-amber-50 to-yellow-50 rounded-xl p-5 border border-amber-200">
                                    <div className="flex items-center gap-2 mb-4">
                                        <div className="w-8 h-8 bg-amber-500 rounded-lg flex items-center justify-center text-white text-sm">
                                            💡
                                        </div>
                                        <h4 className="text-base font-bold text-gray-900">Key AI Insights</h4>
                                        <span className="text-xs bg-amber-500 text-white px-2 py-0.5 rounded-full font-medium">
                                            For Overlay
                                        </span>
                                    </div>
                                    <div className="space-y-2">
                                        {analysisResult.analysis.key_insights.map((insight, index) => (
                                            <div key={index} className="flex items-start gap-3 bg-white/60 rounded-lg p-3 border border-amber-100">
                                                <span className="text-amber-600 font-bold text-sm mt-0.5">{index + 1}</span>
                                                <p className="text-gray-800 text-sm font-medium">{insight}</p>
                                            </div>
                                        ))}
                                    </div>
                                    <p className="text-xs text-amber-700 mt-3 italic">
                                        ↑ These insights are automatically sent to the overlay UI
                                    </p>
                                </div>
                            )}

                            {/* AI Summary Section */}
                            {analysisResult.analysis.summary && (
                                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-5 border border-blue-100">
                                    <div className="flex items-center gap-2 mb-3">
                                        <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white text-sm">
                                            🤖
                                        </div>
                                        <h4 className="text-base font-bold text-gray-900">AI Summary</h4>
                                    </div>
                                    <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                                        {analysisResult.analysis.summary}
                                    </p>
                                </div>
                            )}

                            {/* Extracted Content Section */}
                            {analysisResult.analysis.text_content && (
                                <div>
                                    <div className="flex items-center gap-2 mb-3">
                                        <div className="w-8 h-8 bg-gray-200 rounded-lg flex items-center justify-center text-gray-600 text-sm">
                                            📋
                                        </div>
                                        <h4 className="text-base font-bold text-gray-900">Extracted Content</h4>
                                    </div>
                                    <div className="bg-gray-50 rounded-xl p-4 border border-gray-200 max-h-64 overflow-y-auto">
                                        <pre className="text-sm text-gray-600 whitespace-pre-wrap font-mono">
                                            {analysisResult.analysis.text_content}
                                        </pre>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Modal Footer */}
                        <div className="border-t border-gray-100 p-4 bg-gray-50 flex justify-end">
                            <button
                                onClick={() => setAnalysisResult(null)}
                                className="px-5 py-2.5 bg-gray-900 text-white rounded-lg font-medium hover:bg-gray-800 transition-colors"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MeetingIntelligenceView;
