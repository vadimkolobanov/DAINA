import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getDashboard } from "../../api/client";

interface DashboardBooking {
  id: number;
  client_name: string;
  client_instagram: string | null;
  client_is_new: boolean;
  service_name: string;
  time_start: string;
  time_end: string;
  status: string;
  price: number;
}

interface DashboardData {
  date: string;
  bookings_count: number;
  bookings: DashboardBooking[];
}

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    getDashboard().then(setData);
  }, []);

  if (!data) return <div className="hint">Загрузка...</div>;

  const dateStr = new Date(data.date).toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return (
    <div>
      <motion.h1
        className="page-title"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        {dateStr}
      </motion.h1>

      <motion.div
        className="dashboard-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="dashboard-card__header">Записей сегодня</div>
        <div style={{ fontSize: 32, fontWeight: 700 }}>{data.bookings_count}</div>
        <div className="progress">
          <div
            className="progress__bar"
            style={{ width: `${Math.min(data.bookings_count * 20, 100)}%` }}
          />
        </div>
      </motion.div>

      {data.bookings.length > 0 && (
        <motion.div
          className="dashboard-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="dashboard-card__header">Расписание</div>
          {data.bookings.map((b) => (
            <div key={b.id} className="booking-item">
              <div className="booking-item__time">{b.time_start}</div>
              <div className="booking-item__info">
                <div className="booking-item__name">
                  {b.client_name}
                  {b.client_is_new && <span className="badge badge--new" style={{ marginLeft: 8 }}>NEW</span>}
                </div>
                <div className="booking-item__service">{b.service_name}</div>
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: "var(--accent-dark)" }}>
                {b.price.toLocaleString()}₽
              </div>
            </div>
          ))}
        </motion.div>
      )}

      <div className="tab-nav">
        <button className="tab-nav__item active" onClick={() => navigate("/")}>
          <span className="tab-nav__icon">📊</span>
          Главная
        </button>
        <button className="tab-nav__item" onClick={() => navigate("/clients")}>
          <span className="tab-nav__icon">👥</span>
          Клиенты
        </button>
        <button className="tab-nav__item" onClick={() => navigate("/schedule")}>
          <span className="tab-nav__icon">📅</span>
          График
        </button>
        <button className="tab-nav__item" onClick={() => navigate("/stats")}>
          <span className="tab-nav__icon">📈</span>
          Стат-ка
        </button>
      </div>
    </div>
  );
}
