import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './components/LandingPage';
import DashboardLayout from './components/DashboardLayout';
import DocsView from './components/DocsView';
import OverviewView from './components/OverviewView';
import AnalyticsView from './components/AnalyticsView';
import CalendarView from './components/CalendarView';
import SettingsView from './components/SettingsView';
import MeetingIntelligenceView from './components/MeetingIntelligenceView';

const App: React.FC = () => {
  return (
    <Router>
      <div className="w-full min-h-screen overflow-hidden">
        <Routes>
          <Route path="/" element={<LandingPage />} />

          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<Navigate to="/dashboard/overview" replace />} />
            <Route path="overview" element={<OverviewView />} />
            <Route path="analytics" element={<AnalyticsView />} />
            <Route path="calendar" element={<CalendarView />} />
            <Route path="settings" element={<SettingsView />} />
            <Route path="intelligence" element={<MeetingIntelligenceView />} />
          </Route>

          <Route path="/docs" element={<DocsView />} />

          {/* Catch all redirect to landing */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;