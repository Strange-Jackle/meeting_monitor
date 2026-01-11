import React, { useState } from 'react';
import { Menu } from 'lucide-react';
import Sidebar from './Sidebar';
import { Outlet } from 'react-router-dom';
import NotificationList from './NotificationList';

interface DashboardLayoutProps {
  onNavigateDocs?: () => void;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ onNavigateDocs }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen bg-[#F3F4F6] text-slate-800 font-sans overflow-hidden">
      {/* Mobile Sidebar Toggle (only visible on small screens) */}
      {!isSidebarOpen && (
        <button
          onClick={() => setIsSidebarOpen(true)}
          className="fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md md:hidden"
        >
          <Menu size={20} />
        </button>
      )}

      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      {/* Main Content */}
      <div className={`flex-1 flex flex-col h-full transition-all duration-300 ${isSidebarOpen ? 'md:ml-0' : ''}`}>
        {/* Header */}
        <header className="flex-none h-16 bg-white/80 backdrop-blur-md border-b border-gray-200 flex items-center justify-between px-6 sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="text-gray-500 hover:text-gray-800 transition-colors">
              <Menu size={20} />
            </button>
          </div>

          <div className="flex items-center">
            <NotificationList />
          </div>
        </header>

        {/* Main Content Area - Layout agnostic container */}
        <main className="flex-1 overflow-hidden relative flex flex-col">
          <div className="w-full h-full flex flex-col animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;