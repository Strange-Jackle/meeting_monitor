import React, { useState, useEffect } from 'react';
import { FullScreenCalendar, CalendarData, CalendarEvent } from './ui/fullscreen-calendar';
import { EconomicCalendar, EconomicEvent } from './ui/economic-calendar';
import { X, Clock, Calendar as CalendarIcon, Type, Loader2 } from 'lucide-react';
import { format, isSameDay, parse, parseISO } from 'date-fns';
import { getMeetings, type Meeting } from '../lib/api';

// Initial dummy data
const initialEvents: CalendarData[] = [
  {
    day: new Date("2026-01-02"),
    events: [
      { id: 1, name: "Q1 Planning Session", time: "10:00 AM", datetime: "2026-01-02T10:00" },
      { id: 2, name: "Team Sync", time: "2:00 PM", datetime: "2026-01-02T14:00" },
    ],
  },
  {
    day: new Date("2026-01-07"),
    events: [
      { id: 3, name: "Product Launch Review", time: "2:00 PM", datetime: "2026-01-07T14:00" },
      { id: 4, name: "Marketing Sync", time: "11:00 AM", datetime: "2026-01-07T11:00" },
      { id: 5, name: "Vendor Meeting", time: "4:30 PM", datetime: "2026-01-07T16:30" },
    ],
  },
  {
    day: new Date("2026-01-14"),
    events: [
      { id: 6, name: "Team Building Workshop", time: "11:00 AM", datetime: "2026-01-14T11:00" },
    ],
  },
  {
    day: new Date("2026-01-20"),
    events: [
      { id: 7, name: "Budget Analysis Meeting", time: "3:30 PM", datetime: "2026-01-20T15:30" },
      { id: 8, name: "Sprint Planning", time: "9:00 AM", datetime: "2026-01-20T09:00" },
      { id: 9, name: "Design Review", time: "1:00 PM", datetime: "2026-01-20T13:00" },
    ],
  },
  {
    day: new Date("2026-01-24"),
    events: [
      { id: 10, name: "Client Presentation", time: "10:00 AM", datetime: "2026-01-24T10:00" },
      { id: 11, name: "Team Lunch", time: "12:30 PM", datetime: "2026-01-24T12:30" },
      { id: 12, name: "Project Status Update", time: "2:00 PM", datetime: "2026-01-24T14:00" },
    ],
  },
];

const economicEventsData: EconomicEvent[] = [
  { countryCode: "US", time: "09:30", eventName: "15-Year Mortgage Rate", actual: "6.59%", forecast: null, prior: "6.49%", impact: 'medium' },
  { countryCode: "US", time: "09:30", eventName: "30-Year Mortgage Rate", actual: "7.12%", forecast: null, prior: "7.03%", impact: 'high' },
  { countryCode: "EU", time: "10:30", eventName: "ECB Guindos Speech", actual: null, forecast: null, prior: null, impact: 'low' },
  { countryCode: "CA", time: "11:10", eventName: "BoC Mendes Speech", actual: null, forecast: null, prior: null, impact: 'low' },
  { countryCode: "JP", time: "19:50", eventName: "BoJ Core CPI y/y", actual: "2.8%", forecast: "2.9%", prior: "3.1%", impact: 'high' },
  { countryCode: "AU", time: "21:00", eventName: "RBA Financial Stability Review", actual: null, forecast: null, prior: null, impact: 'medium' },
];

const CalendarView: React.FC = () => {
  const [eventsData, setEventsData] = useState<CalendarData[]>(initialEvents);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newEventTitle, setNewEventTitle] = useState("");
  const [newEventDate, setNewEventDate] = useState(format(new Date(), "yyyy-MM-dd"));
  const [newEventTime, setNewEventTime] = useState("09:00");
  const [loading, setLoading] = useState(true);

  // Fetch meetings from API and merge with calendar
  useEffect(() => {
    async function fetchMeetings() {
      try {
        const response = await getMeetings(50);
        if (response.meetings && response.meetings.length > 0) {
          // Convert meetings to calendar events
          const apiEvents: CalendarData[] = [];

          for (const meeting of response.meetings) {
            if (!meeting.date) continue;

            const meetingDate = new Date(meeting.date);
            const timeStr = format(meetingDate, 'h:mm a');
            const calendarEvent: CalendarEvent = {
              id: meeting.id,
              name: `📹 ${meeting.title}`,
              time: timeStr,
              datetime: meeting.date
            };

            // Find or create day entry
            const existingIdx = apiEvents.findIndex(d => isSameDay(d.day, meetingDate));
            if (existingIdx >= 0) {
              apiEvents[existingIdx].events.push(calendarEvent);
            } else {
              apiEvents.push({ day: meetingDate, events: [calendarEvent] });
            }
          }

          // Merge with initial events
          setEventsData(prev => {
            const merged = [...prev];
            for (const apiDay of apiEvents) {
              const existingIdx = merged.findIndex(d => isSameDay(d.day, apiDay.day));
              if (existingIdx >= 0) {
                // Add API events to existing day, avoiding duplicates
                for (const evt of apiDay.events) {
                  if (!merged[existingIdx].events.find(e => e.id === evt.id)) {
                    merged[existingIdx].events.push(evt);
                  }
                }
              } else {
                merged.push(apiDay);
              }
            }
            return merged;
          });
        }
      } catch (error) {
        console.log('Could not fetch meetings:', error);
        // Continue with dummy data
      } finally {
        setLoading(false);
      }
    }
    fetchMeetings();
  }, []);


  const handleAddEvent = () => {
    if (!newEventTitle || !newEventDate || !newEventTime) return;

    const eventDate = new Date(newEventDate);
    const newEvent: CalendarEvent = {
      id: Date.now(),
      name: newEventTitle,
      time: new Date(`1970-01-01T${newEventTime}`).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
      datetime: `${newEventDate}T${newEventTime}`,
    };

    setEventsData(prev => {
      const existingDayIndex = prev.findIndex(d => isSameDay(d.day, eventDate));
      if (existingDayIndex >= 0) {
        const updated = [...prev];
        updated[existingDayIndex] = {
          ...updated[existingDayIndex],
          events: [...updated[existingDayIndex].events, newEvent]
        };
        return updated;
      } else {
        return [...prev, { day: eventDate, events: [newEvent] }];
      }
    });

    setIsAddModalOpen(false);
    setNewEventTitle("");
    setNewEventTime("09:00");
  };

  return (
    <div className="flex flex-col h-full overflow-hidden relative bg-white">
      <div className="flex-1 overflow-hidden min-h-0">
        <FullScreenCalendar data={eventsData} onAddEvent={() => setIsAddModalOpen(true)} />
      </div>

      <div className="flex-none pt-4 px-4 border-t border-gray-200">
        <EconomicCalendar title="Global Economic Events" events={economicEventsData} className="pb-0" />
      </div>

      {/* Add Event Modal Overlay */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between p-4 border-b border-gray-100 bg-gray-50">
              <h3 className="font-semibold text-gray-900">Add New Event</h3>
              <button onClick={() => setIsAddModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                  <Type size={14} /> Event Title
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                  placeholder="e.g. Project Review"
                  value={newEventTitle}
                  onChange={(e) => setNewEventTitle(e.target.value)}
                  autoFocus
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <CalendarIcon size={14} /> Date
                  </label>
                  <input
                    type="date"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all slate-calendar-picker"
                    value={newEventDate}
                    onChange={(e) => setNewEventDate(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                    <Clock size={14} /> Time
                  </label>
                  <input
                    type="time"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                    value={newEventTime}
                    onChange={(e) => setNewEventTime(e.target.value)}
                  />
                </div>
              </div>
            </div>
            <div className="p-4 border-t border-gray-100 bg-gray-50 flex justify-end gap-3">
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddEvent}
                disabled={!newEventTitle}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg shadow-sm shadow-blue-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Save Event
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CalendarView;