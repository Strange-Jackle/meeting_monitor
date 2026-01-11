/**
 * API Client for Meeting Monitor Dashboard
 * Connects to FastAPI backend for real-time meeting data
 */

// API base URL - dynamically uses same hostname as frontend (for network access)
// If accessed via network IP, API calls will also go to that IP
const getApiBaseUrl = () => {
    // Check for explicit env var first
    if (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_API_URL) {
        return (import.meta as any).env.VITE_API_URL;
    }
    // Use same hostname as current page (works for localhost AND network IPs)
    const hostname = typeof window !== 'undefined' ? window.location.hostname : 'localhost';
    return `http://${hostname}:8000/api/v1`;
};

const API_BASE_URL = getApiBaseUrl();

interface ApiResponse<T> {
    data?: T;
    error?: string;
}

/**
 * Generic fetch wrapper with error handling
 */
async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers,
            },
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`[API] Error fetching ${endpoint}:`, error);
        throw error;
    }
}

// ==================== Meeting Endpoints ====================

export interface Meeting {
    id: number;
    title: string;
    date: string;
    type: string;
    status: string;
    duration?: number;
    summary?: string;
}

export interface MeetingsResponse {
    meetings: Meeting[];
    total: number;
    limit: number;
    offset: number;
}

export async function getMeetings(limit = 20, offset = 0): Promise<MeetingsResponse> {
    return fetchApi<MeetingsResponse>(`/meetings?limit=${limit}&offset=${offset}`);
}

export interface MeetingDetails extends Meeting {
    transcript?: string;
    entities?: Array<{ text: string; label: string; score: number }>;
    battlecards?: Array<{
        competitor: string;
        counter_points?: string[];
        points?: string[];
        web_research?: any;
    }>;
    starred_hints?: Array<{ hint_text: string; status: string }>;
    lead?: {
        name?: string;
        email?: string;
        phone?: string;
        company?: string;
    };
    engagement?: {
        attention?: number;
        interaction?: number;
        sentiment?: number;
        speaking?: number;
        participation?: number;
        clarity?: number;
    };
    sentiment_score?: number;
}

export async function getMeetingDetails(meetingId: number): Promise<MeetingDetails> {
    return fetchApi<MeetingDetails>(`/meetings/${meetingId}`);
}

// ==================== Lead Endpoints ====================

export interface Lead {
    id: number;
    session_id: number;
    name?: string;
    email?: string;
    phone?: string;
    company?: string;
    meeting_title?: string;
    meeting_date?: string;
}

export interface LeadsResponse {
    leads: Lead[];
}

export async function getLeads(limit = 50): Promise<LeadsResponse> {
    return fetchApi<LeadsResponse>(`/leads?limit=${limit}`);
}

// ==================== Analytics Endpoints ====================

export interface AnalyticsOverview {
    meetings_analyzed: number;
    meetings_today: number;
    total_meetings: number;
    ai_insights_generated: number;
    pending_actions: number;
    completed_actions: number;
    audio_issues: number;
    sentiment_score: number;
    engagement_score: number;
    leads_count: number;
    recent_meetings: Meeting[];
    radar_data: Array<{
        subject: string;
        A: number;
        fullMark: number;
    }>;
}

export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
    return fetchApi<AnalyticsOverview>('/analytics/overview');
}

export interface EngagementData {
    data: Array<{
        subject: string;
        A: number;
        fullMark: number;
    }>;
    active_participants: number;
    avg_speaking_time: number;
}

export async function getEngagementData(): Promise<EngagementData> {
    return fetchApi<EngagementData>('/analytics/engagement');
}

// ==================== Session Control ====================

export async function startSession(config?: { capture_mode?: string }): Promise<any> {
    return fetchApi('/start-session', {
        method: 'POST',
        body: JSON.stringify(config || {}),
    });
}

export async function stopSession(): Promise<any> {
    return fetchApi('/stop-session', {
        method: 'POST',
    });
}

export async function getSessionStatus(): Promise<any> {
    return fetchApi('/session-status');
}

// ==================== Overlay Launcher ====================

export async function launchOverlay(): Promise<{ status: string; message: string; pid?: number }> {
    return fetchApi('/launch-overlay', { method: 'POST' });
}

export async function stopOverlay(): Promise<{ status: string; message: string }> {
    return fetchApi('/stop-overlay', { method: 'POST' });
}

export async function getOverlayStatus(): Promise<{ running: boolean; pid?: number }> {
    return fetchApi('/overlay-status');
}

// ==================== Document Endpoints ====================

export interface Document {
    id: number;
    filename: string;
    file_type: string;
    file_size: number;
    uploaded_at: string;
    session_id?: number;
}

export async function uploadDocument(file: File, sessionId?: number): Promise<{ status: string; document: Document }> {
    const formData = new FormData();
    formData.append('file', file);

    let url = `${API_BASE_URL}/documents/upload`;
    if (sessionId) {
        url += `?session_id=${sessionId}`;
    }

    const response = await fetch(url, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
}

export async function getDocuments(sessionId?: number): Promise<{ documents: Document[] }> {
    const url = sessionId ? `/documents?session_id=${sessionId}` : '/documents';
    return fetchApi(url);
}

export async function deleteDocument(docId: number): Promise<{ status: string; id: number }> {
    return fetchApi(`/documents/${docId}`, { method: 'DELETE' });
}

// ==================== Document Analysis (Ollama) ====================

export interface DocumentAnalysis {
    status: string;
    file_type: string;
    pages_analyzed?: number;
    slides_analyzed?: number;
    paragraphs_analyzed?: number;
    text_content?: string;
    summary?: string;
    analysis?: string;
    page_analyses?: string[];
    key_insights?: string[];
}

export async function analyzeDocument(docId: number, prompt?: string): Promise<{
    status: string;
    document_id: number;
    filename: string;
    analysis: DocumentAnalysis;
    insights: string[];
}> {
    const url = prompt
        ? `/documents/${docId}/analyze?prompt=${encodeURIComponent(prompt)}`
        : `/documents/${docId}/analyze`;
    return fetchApi(url, { method: 'POST' });
}

export async function getOllamaHealth(): Promise<{ status: string; models?: string[]; message?: string }> {
    return fetchApi('/ollama/health');
}

export default {
    getMeetings,
    getMeetingDetails,
    getLeads,
    getAnalyticsOverview,
    getEngagementData,
    startSession,
    stopSession,
    getSessionStatus,
    launchOverlay,
    stopOverlay,
    getOverlayStatus,
    uploadDocument,
    getDocuments,
    deleteDocument,
    analyzeDocument,
    getOllamaHealth,
};
