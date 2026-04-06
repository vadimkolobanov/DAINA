import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getAvailableSlots, TimeSlot } from "../api/client";

interface Props {
  date: string;
  serviceId: number;
  selectedTime: string;
  onSelect: (time: string) => void;
}

function groupByPeriod(slots: TimeSlot[]) {
  const morning: TimeSlot[] = [];
  const afternoon: TimeSlot[] = [];
  const evening: TimeSlot[] = [];

  for (const slot of slots) {
    const hour = parseInt(slot.time.split(":")[0]);
    if (hour < 12) morning.push(slot);
    else if (hour < 17) afternoon.push(slot);
    else evening.push(slot);
  }

  return { morning, afternoon, evening };
}

export default function TimeSlots({ date, serviceId, selectedTime, onSelect }: Props) {
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [loading, setLoading] = useState(true);

  const [error, setError] = useState(false);

  useEffect(() => {
    setLoading(true);
    setError(false);
    getAvailableSlots(date, serviceId)
      .then((data) => {
        setSlots(data);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        setError(true);
      });
  }, [date, serviceId]);

  if (loading) {
    return <div className="hint">Загружаю доступное время...</div>;
  }

  if (error) {
    return <div className="hint">Не удалось загрузить слоты. Попробуйте позже.</div>;
  }

  if (slots.length === 0) {
    return <div className="hint">На эту дату нет доступных слотов</div>;
  }

  const groups = groupByPeriod(slots);

  const renderGroup = (title: string, items: TimeSlot[], icon: string) => {
    if (items.length === 0) return null;
    return (
      <div className="time-group">
        <div className="time-group__title">
          {icon} {title}
        </div>
        <div className="time-group__slots">
          {items.map((slot, i) => (
            <motion.button
              key={slot.time}
              className={`time-slot ${selectedTime === slot.time ? "selected" : ""}`}
              onClick={() => onSelect(slot.time)}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              whileTap={{ scale: 0.95 }}
            >
              {slot.time}
            </motion.button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div>
      {renderGroup("Утро", groups.morning, "🌅")}
      {renderGroup("День", groups.afternoon, "☀️")}
      {renderGroup("Вечер", groups.evening, "🌆")}
    </div>
  );
}
