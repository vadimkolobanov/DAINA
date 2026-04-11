import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getDashboard, getPublicConfig } from "../../api/client";
import Skeleton from "../../components/Skeleton";

interface DashboardBooking {
  id: number | string;
  client_id: number | null;
  client_name: string;
  client_instagram: string | null;
  client_is_new: boolean;
  service_name: string;
  time_start: string;
  time_end: string;
  status: string;
  price: number;
  is_manual?: boolean;
  manual_note?: string;
}

interface DashboardData {
  date: string;
  bookings_count: number;
  bookings: DashboardBooking[];
}

const statusBadge: Record<string, { label: string; cls: string }> = {
  pending: { label: "Ожидает", cls: "" },
  confirmed: { label: "Подтв.", cls: "badge--confirmed" },
  completed: { label: "Готово", cls: "badge--confirmed" },
  cancelled: { label: "Отмена", cls: "" },
  no_show: { label: "Не пришёл", cls: "badge--new" },
};

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split("T")[0]);
  const navigate = useNavigate();

  const [error, setError] = useState(false);
  const [botLink, setBotLink] = useState("");
  const [linkCopied, setLinkCopied] = useState(false);

  useEffect(() => {
    setError(false);
    getDashboard(selectedDate)
      .then(setData)
      .catch(() => setError(true));
  }, [selectedDate]);

  useEffect(() => {
    getPublicConfig().then((cfg) => {
      if (cfg.bot_username) {
        const name = cfg.bot_username.replace(/^@/, "");
        setBotLink(`https://t.me/${name}`);
      }
    }).catch(() => {});
  }, []);

  const changeDate = (delta: number) => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + delta);
    setSelectedDate(d.toISOString().split("T")[0]);
  };

  const isToday = selectedDate === new Date().toISOString().split("T")[0];

  const dateStr = new Date(selectedDate).toLocaleDateString("ru-RU", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  return (
    <div>
      {/* Date navigator */}
      <div style={{ display: "flex", gap: 4, justifyContent: "center", marginBottom: 8 }}>
        {Array.from({ length: 7 }, (_, i) => {
          const d = new Date();
          d.setDate(d.getDate() + i);
          const ds = d.toISOString().split("T")[0];
          const dayName = d.toLocaleDateString("ru-RU", { weekday: "short" });
          const dayNum = d.getDate();
          const isSelected = ds === selectedDate;
          return (
            <button
              key={ds}
              className={`filter-chip ${isSelected ? "active" : ""}`}
              style={{ fontSize: 11, padding: "6px 8px", minWidth: 42, textAlign: "center" }}
              onClick={() => setSelectedDate(ds)}
            >
              <div>{dayName}</div>
              <div style={{ fontWeight: 700 }}>{dayNum}</div>
            </button>
          );
        })}
      </div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <button className="calendar__nav" onClick={() => changeDate(-1)} style={{ fontSize: 24 }}>&#8249;</button>
        <div style={{ textAlign: "center" }}>
          <motion.h1
            className="page-title"
            style={{ marginBottom: 4 }}
            key={selectedDate}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {dateStr}
          </motion.h1>
          {!isToday && (
            <button
              className="filter-chip active"
              style={{ fontSize: 11, padding: "4px 12px" }}
              onClick={() => setSelectedDate(new Date().toISOString().split("T")[0])}
            >
              Сегодня
            </button>
          )}
        </div>
        <button className="calendar__nav" onClick={() => changeDate(1)} style={{ fontSize: 24 }}>&#8250;</button>
      </div>

      {error ? (
        <div className="hint">Не удалось загрузить данные</div>
      ) : !data ? (
        <Skeleton count={3} />
      ) : (
        <>
          <motion.div
            className="dashboard-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div className="dashboard-card__header">
              Записей: {data.bookings_count}
            </div>
            <div className="progress">
              <div
                className="progress__bar"
                style={{ width: `${Math.min(data.bookings_count * 20, 100)}%` }}
              />
            </div>
          </motion.div>

          {data.bookings.length === 0 && (
            <div className="hint">Нет записей на этот день</div>
          )}

          {data.bookings.map((b, i) => (
            <motion.div
              key={b.id}
              className="dashboard-card"
              style={{ cursor: "pointer" }}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => b.client_id && navigate(`/client/${b.client_id}`)}
            >
              <div className="booking-item" style={{ borderBottom: "none", padding: 0 }}>
                <div className="booking-item__time">{b.time_start}</div>
                <div className="booking-item__info">
                  <div className="booking-item__name">
                    {b.client_name}
                    {b.client_is_new && <span className="badge badge--new" style={{ marginLeft: 8 }}>NEW</span>}
                    {b.is_manual && <span className="badge" style={{ marginLeft: 8, background: "var(--warning)", color: "white" }}>Личная</span>}
                  </div>
                  <div className="booking-item__service">
                    {b.service_name} &bull; {b.time_start}–{b.time_end}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "var(--accent-dark)" }}>
                    {b.price.toLocaleString()} руб
                  </div>
                  {statusBadge[b.status] && (
                    <span className={`badge ${statusBadge[b.status].cls}`} style={{ marginTop: 4 }}>
                      {statusBadge[b.status].label}
                    </span>
                  )}
                </div>
              </div>
            </motion.div>
          ))}

          {/* Copy bot link */}
          {botLink && (
            <button
              className="btn btn--primary"
              style={{ marginTop: 16, fontSize: 14 }}
              onClick={() => {
                navigator.clipboard.writeText(botLink).then(() => {
                  setLinkCopied(true);
                  setTimeout(() => setLinkCopied(false), 2000);
                });
              }}
            >
              {linkCopied ? "✅ Ссылка скопирована!" : `📋 Скопировать ссылку на бота`}
            </button>
          )}

          {/* Quick actions */}
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => navigate("/all-bookings")}>
              Все записи
            </button>
            <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => navigate("/services")}>
              Услуги
            </button>
            <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => navigate("/settings")}>
              Настройки
            </button>
          </div>
        </>
      )}

      <div className="tab-nav">
        <button className="tab-nav__item active" onClick={() => navigate("/")}>
          <span className="tab-nav__icon">📊</span>
          Главная
        </button>
        <button className="tab-nav__item" onClick={() => navigate("/all-bookings")}>
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
