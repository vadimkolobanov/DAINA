import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { DateAvailability, getAvailableDates } from "../api/client";

interface Props {
  serviceId: number;
  serviceDuration: number;
  selectedDate: string;
  onSelect: (date: string) => void;
}

const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
const MONTHS = [
  "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
];

export default function Calendar({ serviceId, selectedDate, onSelect }: Props) {
  const today = new Date();
  const [month, setMonth] = useState(today.getMonth());
  const [year, setYear] = useState(today.getFullYear());
  const [availability, setAvailability] = useState<Record<string, DateAvailability>>({});
  const [nearestFree, setNearestFree] = useState<string | null>(null);

  useEffect(() => {
    const start = new Date(year, month, 1);
    const end = new Date(year, month + 1, 0);
    let cancelled = false;
    getAvailableDates(
      serviceId,
      start.toISOString().split("T")[0],
      end.toISOString().split("T")[0]
    ).then((dates) => {
      if (cancelled) return;
      const map: Record<string, DateAvailability> = {};
      let nearest: string | null = null;
      for (const d of dates) {
        map[d.date] = d;
        if (d.available && !nearest && new Date(d.date) >= today) {
          nearest = d.date;
        }
      }
      setAvailability(map);
      setNearestFree(nearest);
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [month, year, serviceId]);

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const offset = firstDay === 0 ? 6 : firstDay - 1;

  const prevMonth = () => {
    if (month === 0) {
      setMonth(11);
      setYear(year - 1);
    } else {
      setMonth(month - 1);
    }
  };

  const nextMonth = () => {
    if (month === 11) {
      setMonth(0);
      setYear(year + 1);
    } else {
      setMonth(month + 1);
    }
  };

  const todayStr = today.toISOString().split("T")[0];

  return (
    <div className="calendar">
      <div className="calendar__header">
        <button className="calendar__nav" onClick={prevMonth}>
          &#8249;
        </button>
        <AnimatePresence mode="wait">
          <motion.span
            key={`${year}-${month}`}
            className="calendar__month"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
          >
            {MONTHS[month]} {year}
          </motion.span>
        </AnimatePresence>
        <button className="calendar__nav" onClick={nextMonth}>
          &#8250;
        </button>
      </div>

      <div className="calendar__weekdays">
        {WEEKDAYS.map((d) => (
          <span key={d} className="calendar__weekday">{d}</span>
        ))}
      </div>

      <motion.div
        className="calendar__days"
        key={`${year}-${month}`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        {Array.from({ length: offset }, (_, i) => (
          <span key={`empty-${i}`} />
        ))}
        {Array.from({ length: daysInMonth }, (_, i) => {
          const day = i + 1;
          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const isPast = dateStr < todayStr;
          const isToday = dateStr === todayStr;
          const isSelected = dateStr === selectedDate;
          const info = availability[dateStr];
          const isAvailable = info?.available && !isPast;
          const isDisabled = isPast;

          let className = "calendar__day";
          if (isToday) className += " calendar__day--today";
          if (isSelected) className += " calendar__day--selected";
          if (isAvailable && !isSelected) className += " calendar__day--available";
          if (isDisabled) className += " calendar__day--disabled";
          if (!isAvailable && !isDisabled) className += " calendar__day--unavailable";

          return (
            <motion.button
              key={dateStr}
              className={className}
              onClick={() => isAvailable && onSelect(dateStr)}
              disabled={isDisabled || !isAvailable}
              whileTap={isAvailable ? { scale: 0.9 } : undefined}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.01 }}
            >
              {day}
            </motion.button>
          );
        })}
      </motion.div>

      {nearestFree && !selectedDate && (
        <div className="hint">
          Ближайшее свободное окно:{" "}
          {new Date(nearestFree).toLocaleDateString("ru-RU", {
            weekday: "long",
            day: "numeric",
            month: "long",
          })}
        </div>
      )}
    </div>
  );
}
