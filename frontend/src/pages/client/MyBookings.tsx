import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useTelegram } from "../../hooks/useTelegram";
import { getClientBookings, getClientByTelegram } from "../../api/client";

interface BookingItem {
  id: number;
  service_name: string;
  date: string;
  time_start: string;
  time_end: string;
  status: string;
  price: number;
}

const statusLabel: Record<string, string> = {
  pending: "Ожидает",
  confirmed: "Подтверждено",
  completed: "Завершено",
  cancelled: "Отменено",
  no_show: "Не пришёл",
};

const statusEmoji: Record<string, string> = {
  pending: "🕐",
  confirmed: "✅",
  completed: "✅",
  cancelled: "❌",
  no_show: "⚠️",
};

export default function MyBookings() {
  const { user } = useTelegram();
  const [bookings, setBookings] = useState<BookingItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!user) return;
    getClientByTelegram(user.id)
      .then((client) => getClientBookings(client.id))
      .then((data) => {
        setBookings(data as BookingItem[]);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        setError(true);
      });
  }, [user]);

  if (loading) return <div className="hint">Загрузка...</div>;
  if (error) return <div className="hint">Не удалось загрузить записи</div>;

  return (
    <div>
      <h1 className="page-title">Мои записи</h1>

      {bookings.length === 0 && (
        <div className="hint">У вас пока нет записей</div>
      )}

      {bookings.map((b, i) => (
        <motion.div
          key={b.id}
          className="dashboard-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <strong>{b.service_name}</strong>
            <span>
              {statusEmoji[b.status]} {statusLabel[b.status]}
            </span>
          </div>
          <div style={{ fontSize: 14, color: "var(--tg-theme-hint-color)" }}>
            {new Date(b.date).toLocaleDateString("ru-RU", {
              day: "numeric",
              month: "long",
              weekday: "short",
            })}{" "}
            &bull; {b.time_start} — {b.time_end} &bull; {b.price.toLocaleString()}₽
          </div>
        </motion.div>
      ))}
    </div>
  );
}
