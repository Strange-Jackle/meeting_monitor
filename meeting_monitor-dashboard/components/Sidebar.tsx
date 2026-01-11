import React from 'react';
import {
  LayoutDashboard,
  Calendar,
  Settings,
  Video,
  LogOut,
  X,
  BrainCircuit,
  FileText,
  History
} from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';

interface SidebarProps {
  onNavigateDocs?: () => void;
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ onNavigateDocs, isOpen, onClose }) => {
  const navigate = useNavigate();

  const mainNavItems = [
    { label: 'Meeting Overview', icon: Video, path: '/dashboard/overview' },
    { label: 'Meeting Intelligence', icon: BrainCircuit, path: '/dashboard/intelligence', badge: 'NEW', badgeColor: 'bg-blue-600' },
    { label: 'Meeting History', icon: History, path: '/dashboard/meetings' },
  ];

  const appNavItems = [
    { label: 'Calendar', icon: Calendar, path: '/dashboard/calendar', badge: 'ENHANCED', badgeColor: 'bg-blue-600' },
    { label: 'Scrumboard', icon: LayoutDashboard, path: 'http://10.119.65.52:8069', external: true },
  ];

  return (
    <>
      <div
        className={`fixed inset-y-0 left-0 bg-white border-r border-gray-200 w-64 transform transition-transform duration-300 ease-in-out z-40 ${isOpen ? 'translate-x-0' : '-translate-x-full'
          } md:relative md:translate-x-0 flex flex-col`}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-gray-100 justify-between">
          <div className="flex items-center gap-2 font-bold text-xl text-gray-900 tracking-tight">
            <img src="/wolf_logo.png" alt="TechnoWolf" className="w-10 h-10 rounded-lg object-contain" />
            <span className="font-display font-bold text-xl tracking-tight text-slate-900">TechnoWolf <span className="text-gray-400 font-normal">AI</span></span>
          </div>
          <button onClick={onClose} className="md:hidden text-gray-500">
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto py-6 px-4 space-y-8">
          {/* Main Group */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">
              Menu
            </h3>
            <div className="space-y-1">
              {mainNavItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => window.innerWidth < 768 && onClose()}
                  className={({ isActive }) => `
                    w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group
                    ${isActive
                      ? 'bg-blue-50 text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }
                  `}
                >
                  <div className="flex items-center gap-3">
                    <item.icon size={18} className="group-hover:scale-110 transition-transform duration-200" />
                    {item.label}
                  </div>
                  {item.badge && (
                    <span className={`text-[10px] text-white px-1.5 py-0.5 rounded font-bold ${item.badgeColor}`}>
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          </div>

          {/* Applications Group */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">
              Applications
            </h3>
            <div className="space-y-1">
              {appNavItems.map((item) => (
                item.external ? (
                  <a
                    key={item.path}
                    href={item.path}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => window.innerWidth < 768 && onClose()}
                    className={`
                      w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group
                      text-gray-600 hover:bg-gray-50 hover:text-gray-900
                    `}
                  >
                    <div className="flex items-center gap-3">
                      <item.icon size={18} className="group-hover:scale-110 transition-transform duration-200" />
                      {item.label}
                    </div>
                  </a>
                ) : (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    onClick={() => window.innerWidth < 768 && onClose()}
                    className={({ isActive }) => `
                      w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group
                      ${isActive
                        ? 'bg-blue-50 text-blue-600 shadow-sm'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      }
                    `}
                  >
                    <div className="flex items-center gap-3">
                      <item.icon size={18} className="group-hover:scale-110 transition-transform duration-200" />
                      {item.label}
                    </div>
                    {item.badge && (
                      <span className={`text-[10px] text-white px-1.5 py-0.5 rounded font-bold ${item.badgeColor}`}>
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                )
              ))}
            </div>
          </div>

          {/* Resources Group */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-2">
              Resources
            </h3>
            <div className="space-y-1">
              <button
                onClick={() => { navigate('/docs'); if (window.innerWidth < 768) onClose(); }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-all duration-200 group"
              >
                <FileText size={18} className="group-hover:scale-110 transition-transform duration-200" />
                Documentation
              </button>
            </div>
          </div>

          {/* Preferences Group */}
          <div>
            <div className="space-y-1 mt-4">
              <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 hover:text-red-700 transition-all duration-200 group">
                <LogOut size={18} className="group-hover:scale-110 transition-transform duration-200" />
                Logout
              </button>
            </div>
          </div>

        </div>


      </div>

      {/* Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden backdrop-blur-sm"
          onClick={onClose}
        />
      )}
    </>
  );
};

export default Sidebar;