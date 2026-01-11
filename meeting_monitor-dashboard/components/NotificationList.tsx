import { Bell, Check, Plus, X } from "lucide-react"
import { AnimatePresence, motion } from "framer-motion"
import { useState } from "react"
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover"
import { Button } from "./ui/button"

export default function NotificationList() {
    const [notifications, setNotifications] = useState([
        {
            id: 1,
            title: "Meeting Started",
            description: "Daily Standup has just started.",
            time: "2m ago",
            icon: "video",
            color: "bg-blue-500"
        },
        {
            id: 2,
            title: "New Insight",
            description: "AI detected a potential risk in the last call.",
            time: "15m ago",
            icon: "brain",
            color: "bg-purple-500"
        },
        {
            id: 3,
            title: "Task Assigned",
            description: "Brian assigned you a new task.",
            time: "1h ago",
            icon: "check",
            color: "bg-green-500"
        }
    ])

    const removeNotification = (id: number) => {
        setNotifications((prev) => prev.filter((n) => n.id !== id))
    }

    return (
        <Popover>
            <PopoverTrigger asChild>
                <button className="relative text-gray-500 hover:text-gray-700 outline-none">
                    <Bell size={20} />
                    {notifications.length > 0 && (
                        <span className="absolute -top-1 -right-0.5 flex h-3 w-3">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                        </span>
                    )}
                </button>
            </PopoverTrigger>
            <PopoverContent className="w-80 p-0" align="end">
                <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                    <h4 className="font-semibold text-sm">Notifications</h4>
                    {notifications.length > 0 && (
                        <button
                            onClick={() => setNotifications([])}
                            className="text-xs text-gray-400 hover:text-gray-600"
                        >
                            Clear all
                        </button>
                    )}
                </div>
                <div className="max-h-[300px] overflow-y-auto p-2 space-y-2">
                    <AnimatePresence mode="popLayout">
                        {notifications.length === 0 ? (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="text-center py-8 text-gray-400 text-sm"
                            >
                                No new notifications
                            </motion.div>
                        ) : (
                            notifications.map((notification) => (
                                <motion.div
                                    key={notification.id}
                                    layout
                                    initial={{ opacity: 0, scale: 0.9, y: 20 }}
                                    animate={{ opacity: 1, scale: 1, y: 0 }}
                                    exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
                                    className="relative flex items-start gap-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors group"
                                >
                                    <div className={`mt-0.5 h-2 w-2 rounded-full flex-none ${notification.color}`} />
                                    <div className="flex-1 space-y-1">
                                        <p className="text-sm font-medium leading-none text-gray-900">{notification.title}</p>
                                        <p className="text-xs text-gray-500 line-clamp-2">{notification.description}</p>
                                        <p className="text-[10px] text-gray-400">{notification.time}</p>
                                    </div>
                                    <button
                                        onClick={() => removeNotification(notification.id)}
                                        className="opacity-0 group-hover:opacity-100 absolute top-2 right-2 text-gray-400 hover:text-gray-600 transition-opacity"
                                    >
                                        <X size={14} />
                                    </button>
                                </motion.div>
                            ))
                        )}
                    </AnimatePresence>
                </div>
                <div className="p-2 border-t border-gray-100 bg-gray-50/50">
                    <Button variant="ghost" className="w-full text-xs h-8 text-blue-600 hover:text-blue-700 hover:bg-blue-50">
                        View all activity
                    </Button>
                </div>
            </PopoverContent>
        </Popover>
    )
}
