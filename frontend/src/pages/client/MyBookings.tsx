import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useTelegram } from "../../hooks/useTelegram";
import { getClientBookings, getClientByTelegram, cancelBookingByClient } from "../../api/client";

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
  const { user, haptic, tg } = useTelegram();
  const navigate = useNavigate();
  const [bookings, setBookings] = useState<BookingItem[]>([]);
  const [clientId, setClientId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [confirmCancelId, setConfirmCancelId] = useState<number | null>(null);

  const loadBookings = () => {
    if (!user) return;
    getClientByTelegram(user.id)
      .then((client) => {
        setClientId(client.id);
        return getClientBookings(client.id);
      })
      .then((data) => {
        setBookings(data as BookingItem[]);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
        setError(true);
      });
  };

  useEffect(loadBookings, [user]);

  useEffect(() => {
    tg?.BackButton?.show();
    const back = () => navigate("/");
    tg?.BackButton?.onClick(back);
    return () => {
      tg?.BackButton?.offClick(back);
      tg?.BackButton?.hide();
    };
  }, []);

  const handleCancel = async (bookingId: number) => {
    if (!clientId) return;
    setCancellingId(bookingId);
    try {
      await cancelBookingByClient(bookingId, clientId);
      haptic("medium");
      setBookings((prev) =>
        prev.map((b) => (b.id === bookingId ? { ...b, status: "cancelled" } : b))
      );
    } catch {
      // stay as is
    }
    setCancellingId(null);
    setConfirmCancelId(null);
  };

  if (loading) return <div className="hint">Загрузка...</div>;
  if (error) return <div className="hint">Не удалось загрузить записи</div>;

  const canCancel = (status: string) => status === "pending" || status === "confirmed";

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
            &bull; {b.time_start} — {b.time_end} &bull; {b.price.toLocaleString()} руб
          </div>

          {canCancel(b.status) && confirmCancelId !== b.id && (
            <button
              className="btn btn--danger"
              style={{ marginTop: 10, fontSize: 13, padding: 8 }}
              onClick={() => setConfirmCancelId(b.id)}
            >
              Отменить запись
            </button>
          )}

          {confirmCancelId === b.id && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              style={{ marginTop: 10, textAlign: "center" }}
            >
              <div style={{ fontSize: 13, color: "var(--danger)", marginBottom: 8 }}>
                Точно отменить эту запись?
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  className="btn btn--secondary"
                  style={{ flex: 1, fontSize: 13, padding: 10 }}
                  onClick={() => setConfirmCancelId(null)}
                >
                  Нет
                </button>
                <button
                  className="btn btn--primary"
                  style={{ flex: 1, fontSize: 13, padding: 10, background: "var(--danger)" }}
                  onClick={() => handleCancel(b.id)}
                  disabled={cancellingId === b.id}
                >
                  {cancellingId === b.id ? "Отмена..." : "Да, отменить"}
                </button>
              </div>
            </motion.div>
          )}
        </motion.div>
      ))}

      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => navigate("/contacts")}>
          📞 Контакты мастера
        </button>
        <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => navigate("/")}>
          Назад к услугам
        </button>
      </div>
    </div>
  );
}
