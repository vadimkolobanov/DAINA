import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getAllBookings } from "../../api/client";

interface BookingItem {
  id: number | string;
  client_id: number | null;
  client_name: string;
  client_instagram: string | null;
  service_name: string;
  date: string;
  time_start: string;
  time_end: string;
  status: string;
  price: number;
  is_manual?: boolean;
  manual_note?: string;
}

const statusEmoji: Record<string, string> = {
  pending: "🕐",
  confirmed: "✅",
  completed: "✅",
  cancelled: "❌",
  no_show: "⚠️",
};

const statusLabel: Record<string, string> = {
  pending: "Ожидает",
  confirmed: "Подтверждено",
  completed: "Завершено",
  cancelled: "Отменено",
  no_show: "Не пришёл",
};

export default function AllBookings() {
  const [bookings, setBookings] = useState<BookingItem[]>([]);
  const [filter, setFilter] = useState("all");
  const navigate = useNavigate();

  const [error, setError] = useState(false);

  useEffect(() => {
    setError(false);
    getAllBookings(filter)
      .then(setBookings)
      .catch(() => setError(true));
  }, [filter]);

  const filters = [
    { key: "all", label: "Все" },
    { key: "pending", label: "Ожидают" },
    { key: "confirmed", label: "Подтв." },
    { key: "completed", label: "Готово" },
    { key: "cancelled", label: "Отмены" },
  ];

  return (
    <div>
      <h1 className="page-title">Все записи</h1>

      <div className="filter-chips">
        {filters.map((f) => (
          <button
            key={f.key}
            className={`filter-chip ${filter === f.key ? "active" : ""}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {error && <div className="hint">Не удалось загрузить записи</div>}
      {!error && bookings.length === 0 && <div className="hint">Нет записей</div>}

      {bookings.map((b, i) => (
        <motion.div
          key={b.id}
          className="dashboard-card"
          style={{ cursor: "pointer", marginBottom: 8 }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.02 }}
          onClick={() => b.client_id && navigate(`/client/${b.client_id}`)}
        >
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
            <div>
              <strong>{b.client_name}</strong>
              {b.is_manual && <span className="badge" style={{ marginLeft: 8, background: "var(--warning)", color: "white" }}>Личная</span>}
              {b.client_instagram && (
                <span style={{ fontSize: 12, color: "var(--tg-theme-hint-color)", marginLeft: 6 }}>
                  @{b.client_instagram}
                </span>
              )}
            </div>
            <span>
              {statusEmoji[b.status]} {statusLabel[b.status]}
            </span>
          </div>
          <div style={{ fontSize: 13, color: "var(--tg-theme-hint-color)" }}>
            {b.service_name} &bull;{" "}
            {new Date(b.date).toLocaleDateString("ru-RU", {
              day: "numeric",
              month: "short",
              weekday: "short",
            })}{" "}
            &bull; {b.time_start}–{b.time_end} &bull; {b.price.toLocaleString()} руб
          </div>
        </motion.div>
      ))}

      <button
        className="btn btn--secondary"
        style={{ marginTop: 16 }}
        onClick={() => navigate("/")}
      >
        Назад
      </button>

      <div className="tab-nav">
        <button className="tab-nav__item" onClick={() => navigate("/")}>
          <span className="tab-nav__icon">📊</span>
          Главная
        </button>
        <button className="tab-nav__item active" onClick={() => navigate("/all-bookings")}>
          <span className="tab-nav__icon">📋</span>
          Записи
        </button>
        <button className="tab-nav__item" onClick={() => navigate("/clients")}>
          <span className="tab-nav__icon">👥</span>
          Клиенты
        </button>
        <button className="tab-nav__item" onClick={() => navigate("/slots")}>
          <span className="tab-nav__icon">📅</span>
          Окошки
        </button>
        <button className="tab-nav__item" onClick={() => navigate("/stats")}>
          <span className="tab-nav__icon">📈</span>
          Стат-ка
        </button>
      </div>
    </div>
  );
}
