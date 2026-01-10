// components/ui/economic-calendar.tsx
import * as React from "react";
import { motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Code2 } from "lucide-react";
import { cn } from "@/lib/utils"; // Assuming you have a `cn` utility from shadcn

// Type definition for a single economic event
export interface EconomicEvent {
    countryCode: string;
    time: string;
    eventName: string;
    actual: string | null;
    forecast: string | null;
    prior: string | null;
    impact: 'high' | 'medium' | 'low';
}

// Props for the main component
interface EconomicCalendarProps {
    title: string;
    events: EconomicEvent[];
    className?: string;
}

// A simple volatility icon component
const VolatilityIcon = ({ impact }: { impact: EconomicEvent['impact'] }) => {
    const barCount = impact === 'high' ? 3 : impact === 'medium' ? 2 : 1;
    return (
        <div className="flex items-end gap-0.5 h-4">
            {Array.from({ length: 3 }).map((_, i) => (
                <span
                    key={i}
                    className={cn(
                        "w-1 rounded-full",
                        i === 0 ? "h-2" : i === 1 ? "h-3" : "h-4",
                        i < barCount ? "bg-slate-800" : "bg-gray-200"
                    )}
                />
            ))}
        </div>
    );
};

export const EconomicCalendar = React.forwardRef<
    HTMLDivElement,
    EconomicCalendarProps
>(({ title, events, className }, ref) => {
    const scrollContainerRef = React.useRef<HTMLDivElement>(null);
    const [canScrollLeft, setCanScrollLeft] = React.useState(false);
    const [canScrollRight, setCanScrollRight] = React.useState(true);

    // Function to handle scrolling and update button states
    const handleScroll = () => {
        const container = scrollContainerRef.current;
        if (container) {
            const scrollLeft = container.scrollLeft;
            const scrollWidth = container.scrollWidth;
            const clientWidth = container.clientWidth;
            setCanScrollLeft(scrollLeft > 0);
            setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 1);
        }
    };

    // Scroll function for navigation buttons
    const scroll = (direction: "left" | "right") => {
        const container = scrollContainerRef.current;
        if (container) {
            const scrollAmount = container.clientWidth * 0.8;
            container.scrollBy({
                left: direction === "left" ? -scrollAmount : scrollAmount,
                behavior: "smooth",
            });
        }
    };

    React.useEffect(() => {
        const container = scrollContainerRef.current;
        if (container) {
            container.addEventListener("scroll", handleScroll);
            handleScroll(); // Initial check
            return () => container.removeEventListener("scroll", handleScroll);
        }
    }, [events]);

    // Framer Motion variants for animations
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1,
            },
        },
    };

    const itemVariants = {
        hidden: { y: 20, opacity: 0 },
        visible: {
            y: 0,
            opacity: 1,
            transition: {
                type: "spring",
                stiffness: 100,
                damping: 14,
            },
        },
    };

    return (
        <div ref={ref} className={cn("w-full font-sans", className)}>
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                    {title}
                </h2>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => scroll("left")}
                        disabled={!canScrollLeft}
                        aria-label="Scroll left"
                        className={cn(
                            "p-2 rounded-full border border-gray-200 transition-colors",
                            !canScrollLeft ? "opacity-50 cursor-not-allowed bg-gray-50" : "bg-white hover:bg-gray-50 shadow-sm"
                        )}
                    >
                        <ChevronLeft className="h-4 w-4 text-gray-600" />
                    </button>

                    <button
                        onClick={() => scroll("right")}
                        disabled={!canScrollRight}
                        aria-label="Scroll right"
                        className={cn(
                            "p-2 rounded-full border border-gray-200 transition-colors",
                            !canScrollRight ? "opacity-50 cursor-not-allowed bg-gray-50" : "bg-white hover:bg-gray-50 shadow-sm"
                        )}
                    >
                        <ChevronRight className="h-4 w-4 text-gray-600" />
                    </button>
                </div>
            </div>

            {/* Scrollable Events Container */}
            <div
                ref={scrollContainerRef}
                className="flex gap-4 overflow-x-auto pb-4 scroll-smooth scrollbar-hide no-scrollbar"
                style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
            >
                <motion.div
                    className="flex flex-nowrap gap-4"
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                >
                    {events.map((event, index) => (
                        <motion.div
                            key={index}
                            variants={itemVariants}
                            className="flex-shrink-0 w-72 bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow duration-300"
                        >
                            <div className="flex justify-between items-center mb-4">
                                <div className="flex items-center gap-2">
                                    <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded">
                                        {event.time}
                                    </span>
                                </div>
                                <VolatilityIcon impact={event.impact} />
                            </div>

                            <div className="flex items-center gap-3 mb-5">
                                <img
                                    // Using FlagCDN for reliable flags
                                    src={`https://flagcdn.com/w40/${event.countryCode.toLowerCase()}.png`}
                                    alt={`${event.countryCode} flag`}
                                    className="h-8 w-8 rounded-full object-cover border border-gray-100 shadow-sm shrink-0"
                                />
                                <h3 className="font-bold text-gray-900 leading-tight line-clamp-2">{event.eventName}</h3>
                            </div>

                            <div className="grid grid-cols-3 gap-2 text-center text-xs">
                                <div className="bg-gray-50 rounded-lg p-2">
                                    <p className="text-gray-500 mb-1">Actual</p>
                                    <p className="font-bold text-gray-900">{event.actual ?? "—"}</p>
                                </div>
                                <div className="bg-gray-50 rounded-lg p-2">
                                    <p className="text-gray-500 mb-1">Forecast</p>
                                    <p className="font-bold text-gray-900">{event.forecast ?? "—"}</p>
                                </div>
                                <div className="bg-gray-50 rounded-lg p-2">
                                    <p className="text-gray-500 mb-1">Prior</p>
                                    <p className="font-bold text-gray-900">{event.prior ?? "—"}</p>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </motion.div>
            </div>
        </div>
    );
});

EconomicCalendar.displayName = "EconomicCalendar";
