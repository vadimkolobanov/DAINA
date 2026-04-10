import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { getAvailableSlots, getWaitlistPosition, joinWaitlist, leaveWaitlist, TimeSlot } from "../api/client";

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

  // Waitlist state — must be declared before any conditional returns
  const [inWaitlist, setInWaitlist] = useState(false);
  const [waitlistPosition, setWaitlistPosition] = useState<number | null>(null);
  const [waitlistLoading, setWaitlistLoading] = useState(false);

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

  useEffect(() => {
    if (slots.length === 0 && !loading && !error) {
      getWaitlistPosition(serviceId)
        .then((data) => {
          setInWaitlist(data.in_waitlist);
          setWaitlistPosition(data.position);
        })
        .catch(() => {});
    }
  }, [slots, loading, serviceId]);

  const handleJoinWaitlist = async () => {
    setWaitlistLoading(true);
    try {
      const result = await joinWaitlist(serviceId);
      setInWaitlist(true);
      setWaitlistPosition(result.position);
    } catch {}
    setWaitlistLoading(false);
  };

  const handleLeaveWaitlist = async () => {
    setWaitlistLoading(true);
    try {
      await leaveWaitlist(serviceId);
      setInWaitlist(false);
      setWaitlistPosition(null);
    } catch {}
    setWaitlistLoading(false);
  };

  if (slots.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "20px 0" }}>
        <div className="hint" style={{ marginBottom: 16 }}>
          На эту дату нет свободных окошек
        </div>
        {inWaitlist ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="dashboard-card" style={{ textAlign: "center" }}>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>
                Вы в очереди ожидания
              </div>
              {waitlistPosition && (
                <div style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", marginBottom: 12 }}>
                  Ваша позиция: {waitlistPosition}
                </div>
              )}
              <div style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", marginBottom: 12 }}>
                Когда появится окошко — вы получите уведомление в Telegram
              </div>
              <button
                className="btn btn--secondary"
                onClick={handleLeaveWaitlist}
                disabled={waitlistLoading}
                style={{ fontSize: 14 }}
              >
                Отменить ожидание
              </button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", marginBottom: 16, lineHeight: 1.5 }}>
              Когда мастер откроет новые окошки или освободятся занятые,
              вы получите уведомление и сможете записаться первыми
            </div>
            <button
              className="btn btn--primary"
              onClick={handleJoinWaitlist}
              disabled={waitlistLoading}
            >
              {waitlistLoading ? "Подождите..." : "Записаться в ожидание"}
            </button>
          </motion.div>
        )}
      </div>
    );
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
