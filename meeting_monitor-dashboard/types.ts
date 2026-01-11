export type ViewState = 'LANDING' | 'DASHBOARD' | 'DOCS';

export type DashboardTab = 'OVERVIEW' | 'ANALYTICS' | 'CALENDAR' | 'SETTINGS' | 'MEETING_INTELLIGENCE';

export interface NavItem {
  label: string;
  icon: any; // Using any for Lucide icons component type
  id: DashboardTab;
  badge?: string;
  badgeColor?: string;
}

// Global declaration for CDNs
declare global {
  interface Window {
    gsap: any;
    anime: any;
  }
}