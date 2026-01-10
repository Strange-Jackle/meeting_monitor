"use client"

import * as React from "react"
import {
    add,
    eachDayOfInterval,
    endOfMonth,
    endOfWeek,
    format,
    getDay,
    isEqual,
    isSameDay,
    isSameMonth,
    isToday,
    parse,
    startOfToday,
    startOfWeek,
} from "date-fns"
import {
    ChevronLeftIcon,
    ChevronRightIcon,
    PlusCircleIcon,
    SearchIcon,
} from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useMediaQuery } from "@/hooks/use-media-query"

export interface CalendarEvent {
    id: number
    name: string
    time: string
    datetime: string
}

export interface CalendarData {
    day: Date
    events: CalendarEvent[]
}

interface FullScreenCalendarProps {
    data: CalendarData[]
    onAddEvent?: () => void
}

const colStartClasses = [
    "",
    "col-start-2",
    "col-start-3",
    "col-start-4",
    "col-start-5",
    "col-start-6",
    "col-start-7",
]

export function FullScreenCalendar({ data, onAddEvent }: FullScreenCalendarProps) {
    const today = startOfToday()
    const [selectedDay, setSelectedDay] = React.useState(today)
    const [currentMonth, setCurrentMonth] = React.useState(
        format(today, "MMM-yyyy"),
    )
    const firstDayCurrentMonth = parse(currentMonth, "MMM-yyyy", new Date())
    const isDesktop = useMediaQuery("(min-width: 768px)")

    const days = eachDayOfInterval({
        start: startOfWeek(firstDayCurrentMonth),
        end: endOfWeek(endOfMonth(firstDayCurrentMonth)),
    })

    // Calculate the number of weeks to dynamically size the grid rows
    const weeks = Math.ceil(days.length / 7)

    function previousMonth() {
        const firstDayNextMonth = add(firstDayCurrentMonth, { months: -1 })
        setCurrentMonth(format(firstDayNextMonth, "MMM-yyyy"))
    }

    function nextMonth() {
        const firstDayNextMonth = add(firstDayCurrentMonth, { months: 1 })
        setCurrentMonth(format(firstDayNextMonth, "MMM-yyyy"))
    }

    function goToToday() {
        setCurrentMonth(format(today, "MMM-yyyy"))
    }

    return (
        <div className="flex flex-1 flex-col h-full bg-white">
            {/* Calendar Header */}
            <div className="flex flex-col space-y-4 p-4 md:flex-row md:items-center md:justify-between md:space-y-0 border-b border-gray-100 flex-none">
                <div className="flex flex-auto">
                    <div className="flex items-center gap-4">
                        <div className="hidden w-16 flex-col items-center justify-center rounded-lg border bg-muted p-0.5 md:flex">
                            <h1 className="p-1 text-[10px] uppercase text-muted-foreground font-semibold">
                                {format(today, "MMM")}
                            </h1>
                            <div className="flex w-full items-center justify-center rounded-md border bg-background p-0.5 text-xl font-bold">
                                <span>{format(today, "d")}</span>
                            </div>
                        </div>
                        <div className="flex flex-col">
                            <h2 className="text-xl font-bold text-foreground">
                                {format(firstDayCurrentMonth, "MMMM yyyy")}
                            </h2>
                            <p className="text-sm text-muted-foreground font-medium">
                                {format(firstDayCurrentMonth, "MMM d, yyyy")} -{" "}
                                {format(endOfMonth(firstDayCurrentMonth), "MMM d, yyyy")}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="flex flex-col items-center gap-4 md:flex-row md:gap-4">
                    <div className="inline-flex w-full -space-x-px rounded-lg shadow-sm shadow-black/5 md:w-auto rtl:space-x-reverse">
                        <Button
                            onClick={previousMonth}
                            className="rounded-none shadow-none first:rounded-s-lg last:rounded-e-lg focus-visible:z-10 h-9"
                            variant="outline"
                            size="icon"
                            aria-label="Navigate to previous month"
                        >
                            <ChevronLeftIcon size={16} strokeWidth={2} aria-hidden="true" />
                        </Button>
                        <Button
                            onClick={goToToday}
                            className="w-full rounded-none shadow-none first:rounded-s-lg last:rounded-e-lg focus-visible:z-10 md:w-auto h-9 font-medium"
                            variant="outline"
                        >
                            Today
                        </Button>
                        <Button
                            onClick={nextMonth}
                            className="rounded-none shadow-none first:rounded-s-lg last:rounded-e-lg focus-visible:z-10 h-9"
                            variant="outline"
                            size="icon"
                            aria-label="Navigate to next month"
                        >
                            <ChevronRightIcon size={16} strokeWidth={2} aria-hidden="true" />
                        </Button>
                    </div>

                    <div className="hidden md:block h-6 w-px bg-gray-200" />

                    <Button onClick={onAddEvent} className="w-full gap-2 md:w-auto bg-blue-600 hover:bg-blue-700 text-white h-9 shadow-sm shadow-blue-500/20">
                        <PlusCircleIcon size={16} strokeWidth={2} aria-hidden="true" />
                        <span className="font-medium">New Event</span>
                    </Button>
                </div>
            </div>

            {/* Calendar Grid */}
            <div className="md:flex md:flex-auto md:flex-col h-full overflow-hidden">
                {/* Week Days Header */}
                <div className="grid grid-cols-7 border-b text-center text-xs font-semibold leading-6 md:flex-none text-gray-500 bg-gray-50/50">
                    <div className="border-r py-2.5">Sun</div>
                    <div className="border-r py-2.5">Mon</div>
                    <div className="border-r py-2.5">Tue</div>
                    <div className="border-r py-2.5">Wed</div>
                    <div className="border-r py-2.5">Thu</div>
                    <div className="border-r py-2.5">Fri</div>
                    <div className="py-2.5">Sat</div>
                </div>

                {/* Calendar Days */}
                <div className="flex text-xs leading-6 md:flex-auto h-full overflow-hidden">
                    <div
                        className="hidden w-full md:grid md:grid-cols-7 h-full"
                        style={{ gridTemplateRows: `repeat(${weeks}, minmax(0, 1fr))` }}
                    >
                        {days.map((day, dayIdx) =>
                            !isDesktop ? (
                                <button
                                    onClick={() => setSelectedDay(day)}
                                    // ... existing mobile code ...
                                    key={dayIdx} // Keeping key here, logic below implies mobile render
                                    type="button"
                                    className={cn(
                                        isEqual(day, selectedDay) && "text-primary-foreground",
                                        !isEqual(day, selectedDay) &&
                                        !isToday(day) &&
                                        isSameMonth(day, firstDayCurrentMonth) &&
                                        "text-foreground",
                                        !isEqual(day, selectedDay) &&
                                        !isToday(day) &&
                                        !isSameMonth(day, firstDayCurrentMonth) &&
                                        "text-muted-foreground",
                                        (isEqual(day, selectedDay) || isToday(day)) &&
                                        "font-semibold",
                                        "flex h-14 flex-col border-b border-r px-3 py-2 hover:bg-muted focus:z-10",
                                    )}
                                >
                                    {/* ... mobile content ... */}
                                    <time
                                        dateTime={format(day, "yyyy-MM-dd")}
                                        className={cn(
                                            "ml-auto flex size-6 items-center justify-center rounded-full",
                                            isEqual(day, selectedDay) &&
                                            isToday(day) &&
                                            "bg-blue-600 text-white",
                                            isEqual(day, selectedDay) &&
                                            !isToday(day) &&
                                            "bg-blue-600 text-white",
                                        )}
                                    >
                                        {format(day, "d")}
                                    </time>
                                </button>
                            ) : (
                                <div
                                    key={dayIdx}
                                    onClick={() => setSelectedDay(day)}
                                    className={cn(
                                        dayIdx === 0 && colStartClasses[getDay(day)],
                                        !isSameMonth(day, firstDayCurrentMonth) &&
                                        "bg-gray-50/30 text-muted-foreground",
                                        "relative flex flex-col border-b border-r hover:bg-gray-50 focus:z-10 min-h-0 h-full",
                                        !isEqual(day, selectedDay) && "hover:bg-gray-50",
                                    )}
                                >
                                    <header className="flex items-center justify-between p-2.5">
                                        <button
                                            type="button"
                                            className={cn(
                                                isEqual(day, selectedDay) && "text-white",
                                                !isEqual(day, selectedDay) &&
                                                !isToday(day) &&
                                                isSameMonth(day, firstDayCurrentMonth) &&
                                                "text-gray-700",
                                                !isEqual(day, selectedDay) &&
                                                !isToday(day) &&
                                                !isSameMonth(day, firstDayCurrentMonth) &&
                                                "text-gray-400",
                                                isEqual(day, selectedDay) &&
                                                isToday(day) &&
                                                "border-none bg-blue-600",
                                                isEqual(day, selectedDay) &&
                                                !isToday(day) &&
                                                "bg-blue-600",
                                                (isEqual(day, selectedDay) || isToday(day)) &&
                                                "font-semibold",
                                                "flex h-7 w-7 items-center justify-center rounded-full text-xs hover:bg-blue-100/50 transition-colors",
                                            )}
                                        >
                                            <time dateTime={format(day, "yyyy-MM-dd")}>
                                                {format(day, "d")}
                                            </time>
                                        </button>
                                    </header>
                                    <div className="flex-1 p-2.5 overflow-hidden">
                                        {data
                                            .filter((event) => isSameDay(event.day, day))
                                            .map((day) => (
                                                <div key={day.day.toString()} className="space-y-1.5">
                                                    {day.events.slice(0, 3).map((event) => (
                                                        <div
                                                            key={event.id}
                                                            className="flex flex-col items-start gap-1 rounded px-2 py-1 text-[10px] leading-tight bg-blue-50 text-blue-700 border border-blue-100 hover:bg-blue-100 transition-colors cursor-pointer"
                                                        >
                                                            <p className="font-semibold leading-none truncate w-full">
                                                                {event.name}
                                                            </p>
                                                            <p className="leading-none text-blue-500/80 text-[9px]">
                                                                {event.time}
                                                            </p>
                                                        </div>
                                                    ))}
                                                    {day.events.length > 3 && (
                                                        <div className="text-[10px] text-gray-500 pl-1 font-medium">
                                                            + {day.events.length - 3} more
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                    </div>
                                </div>
                            ),
                        )}
                    </div>

                    <div className="isolate grid w-full grid-cols-7 grid-rows-5 border-x md:hidden">
                        {days.map((day, dayIdx) => (
                            <button
                                onClick={() => setSelectedDay(day)}
                                key={dayIdx}
                                type="button"
                                className={cn(
                                    isEqual(day, selectedDay) && "text-primary-foreground",
                                    !isEqual(day, selectedDay) &&
                                    !isToday(day) &&
                                    isSameMonth(day, firstDayCurrentMonth) &&
                                    "text-foreground",
                                    !isEqual(day, selectedDay) &&
                                    !isToday(day) &&
                                    !isSameMonth(day, firstDayCurrentMonth) &&
                                    "text-muted-foreground",
                                    (isEqual(day, selectedDay) || isToday(day)) &&
                                    "font-semibold",
                                    "flex h-14 flex-col border-b border-r px-3 py-2 hover:bg-muted focus:z-10",
                                )}
                            >
                                <time
                                    dateTime={format(day, "yyyy-MM-dd")}
                                    className={cn(
                                        "ml-auto flex size-6 items-center justify-center rounded-full",
                                        isEqual(day, selectedDay) &&
                                        isToday(day) &&
                                        "bg-blue-600 text-white",
                                        isEqual(day, selectedDay) &&
                                        !isToday(day) &&
                                        "bg-blue-600 text-white",
                                    )}
                                >
                                    {format(day, "d")}
                                </time>
                                {data.filter((date) => isSameDay(date.day, day)).length > 0 && (
                                    <div>
                                        {data
                                            .filter((date) => isSameDay(date.day, day))
                                            .map((date) => (
                                                <div
                                                    key={date.day.toString()}
                                                    className="-mx-0.5 mt-auto flex flex-wrap-reverse"
                                                >
                                                    {date.events.map((event) => (
                                                        <span
                                                            key={event.id}
                                                            className="mx-0.5 mt-1 h-1.5 w-1.5 rounded-full bg-blue-400"
                                                        />
                                                    ))}
                                                </div>
                                            ))}
                                    </div>
                                )}
                            </button>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
