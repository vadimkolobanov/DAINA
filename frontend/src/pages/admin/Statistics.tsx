import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getStats } from "../../api/client";

interface Stats {
  period: string;
  total_bookings: number;
  completed: number;
  cancelled: number;
  no_show: number;
  revenue: number;
  average_check: number;
  new_clients: number;
  completion_rate: number;
}

export default function Statistics() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [period, setPeriod] = useState("month");
  const navigate = useNavigate();

  useEffect(() => {
    getStats(period).then(setStats);
  }, [period]);

  if (!stats) return <div className="hint">Загрузка...</div>;

  return (
    <div>
      <h1 className="page-title">Статистика</h1>

      <div className="filter-chips">
        {[
          { key: "week", label: "Неделя" },
          { key: "month", label: "Месяц" },
          { key: "all", label: "Всё время" },
        ].map((p) => (
          <button
            key={p.key}
            className={`filter-chip ${period === p.key ? "active" : ""}`}
            onClick={() => setPeriod(p.key)}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="stat-grid">
        <motion.div
          className="stat-card"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <div className="stat-card__value">{stats.revenue.toLocaleString()}₽</div>
          <div className="stat-card__label">Выручка</div>
        </motion.div>
        <motion.div
          className="stat-card"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.05 }}
        >
          <div className="stat-card__value">{stats.total_bookings}</div>
          <div className="stat-card__label">Записей</div>
        </motion.div>
        <motion.div
          className="stat-card"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
        >
          <div className="stat-card__value">{stats.average_check.toLocaleString()}₽</div>
          <div className="stat-card__label">Средний чек</div>
        </motion.div>
        <motion.div
          className="stat-card"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.15 }}
        >
          <div className="stat-card__value">{stats.completion_rate}%</div>
          <div className="stat-card__label">Выполнено</div>
        </motion.div>
      </div>

      <motion.div
        className="dashboard-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="dashboard-card__header">Детали</div>
        <div className="confirmation__row">
          <span className="confirmation__label">Выполнено</span>
          <span className="confirmation__value">{stats.completed}</span>
        </div>
        <div className="confirmation__row">
          <span className="confirmation__label">Отмены</span>
          <span className="confirmation__value">{stats.cancelled}</span>
        </div>
        <div className="confirmation__row">
          <span className="confirmation__label">No-show</span>
          <span className="confirmation__value">{stats.no_show}</span>
        </div>
        <div className="confirmation__row">
          <span className="confirmation__label">Новых клиентов</span>
          <span className="confirmation__value">{stats.new_clients}</span>
        </div>
      </motion.div>

      <div className="tab-nav">
        <button className="tab-nav__item" onClick={() => navigate("/")}>
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
        <button className="tab-nav__item active" onClick={() => navigate("/stats")}>
          <span className="tab-nav__icon">📈</span>
          Стат-ка
        </button>
      </div>
    </div>
  );
}
