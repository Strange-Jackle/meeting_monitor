import React, { useState } from 'react';
import {
  Search,
  Menu,
} from 'lucide-react';
import Sidebar from './Sidebar';
import { Outlet, useLocation } from 'react-router-dom';
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu"
import NotificationList from './NotificationList';
import { cn } from '@/lib/utils';

interface DashboardLayoutProps {
  onNavigateDocs?: () => void;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ onNavigateDocs }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const location = useLocation();

  const getBreadcrumb = () => {
    const path = location.pathname.split('/').pop()?.toUpperCase();
    const map: Record<string, string> = {
      'ANALYTICS': 'Analytics & Insights',
      'CALENDAR': 'Calendar',
      'SETTINGS': 'Settings',
      'OVERVIEW': 'Overview',
      'INTELLIGENCE': 'Meeting Intelligence'
    };
    return map[path || ''] || 'Dashboard';
  };

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
            <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="hidden md:block text-gray-500 hover:text-gray-800 transition-colors">
              <Menu size={20} />
            </button>

            {/* Interactive Navigation Menu */}
            <NavigationMenu className="hidden md:flex">
              <NavigationMenuList>
                <NavigationMenuItem>
                  <NavigationMenuTrigger className="bg-transparent hover:bg-gray-100 text-gray-500 h-8 px-3">Home</NavigationMenuTrigger>
                  <NavigationMenuContent>
                    <ul className="grid gap-3 p-4 md:w-[400px] lg:w-[500px] lg:grid-cols-[.75fr_1fr]">
                      <li className="row-span-3">
                        <NavigationMenuLink asChild>
                          <a
                            className="flex h-full w-full select-none flex-col justify-end rounded-md bg-gradient-to-b from-blue-500 to-indigo-600 p-6 no-underline outline-none focus:shadow-md"
                            href="/"
                          >
                            <div className="mb-2 mt-4 text-lg font-medium text-white">
                              Meeting Monitor AI
                            </div>
                            <p className="text-sm leading-tight text-blue-100">
                              Your intelligent assistant for productive meetings.
                            </p>
                          </a>
                        </NavigationMenuLink>
                      </li>
                      <ListItem href="/dashboard/overview" title="Overview">
                        Get a quick summary of your meeting activities.
                      </ListItem>
                      <ListItem href="/dashboard/analytics" title="Analytics">
                        Deep dive into meeting metrics and insights.
                      </ListItem>
                      <ListItem href="/dashboard/intelligence" title="Intelligence">
                        AI-powered analysis and recommendations.
                      </ListItem>
                    </ul>
                  </NavigationMenuContent>
                </NavigationMenuItem>

                <NavigationMenuItem>
                  <NavigationMenuTrigger className="bg-transparent hover:bg-gray-100 text-gray-500 h-8 px-3">Apps</NavigationMenuTrigger>
                  <NavigationMenuContent>
                    <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px] ">
                      <ListItem title="Calendar" href="/dashboard/calendar">
                        Manage your schedule and view upcoming events.
                      </ListItem>
                      <ListItem title="Tasks" href="/dashboard/settings">
                        Track your to-dos and project progress.
                      </ListItem>
                      <ListItem title="Scrumboard" href="/dashboard/overview">
                        Agile project management board.
                      </ListItem>
                      <ListItem title="Meeting Intelligence" href="/dashboard/intelligence">
                        Real-time meeting assistance.
                      </ListItem>
                    </ul>
                  </NavigationMenuContent>
                </NavigationMenuItem>

                <NavigationMenuItem>
                  <div className="flex items-center px-3 text-sm font-medium text-gray-900">
                    /{getBreadcrumb()}
                  </div>
                </NavigationMenuItem>
              </NavigationMenuList>
            </NavigationMenu>

            {/* Fallback for Mobile (simple logic for now) */}
            <div className="md:hidden flex items-center gap-2 text-sm text-gray-500">
              <span className="font-semibold text-gray-900">{getBreadcrumb()}</span>
            </div>

          </div>

          <div className="flex items-center gap-6">
            <div className="relative hidden sm:block group">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-blue-500 transition-colors" size={16} />
              <input
                type="text"
                placeholder="Search..."
                className="pl-10 pr-4 py-2 bg-gray-100/50 hover:bg-gray-100 border border-transparent focus:bg-white focus:border-blue-200 rounded-lg text-sm focus:ring-4 focus:ring-blue-500/10 focus:outline-none w-64 transition-all"
              />
            </div>

            <NotificationList />

            <div className="flex items-center gap-3 pl-6 border-l border-gray-200">
              <div className="text-right hidden sm:block">
                <div className="text-sm font-medium text-gray-900">Brian Hughes</div>
                <div className="text-xs text-gray-500">Admin</div>
              </div>
              <img
                src="https://picsum.photos/100/100"
                alt="Profile"
                className="w-10 h-10 rounded-full border-2 border-white shadow-sm object-cover"
              />
            </div>
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

const ListItem = React.forwardRef<
  React.ElementRef<"a">,
  React.ComponentPropsWithoutRef<"a">
>(({ className, title, children, ...props }, ref) => {
  return (
    <li>
      <NavigationMenuLink asChild>
        <a
          ref={ref}
          className={cn(
            "block select-none space-y-1 rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground",
            className
          )}
          {...props}
        >
          <div className="text-sm font-medium leading-none">{title}</div>
          <p className="line-clamp-2 text-sm leading-snug text-muted-foreground">
            {children}
          </p>
        </a>
      </NavigationMenuLink>
    </li>
  )
})
ListItem.displayName = "ListItem"

export default DashboardLayout;