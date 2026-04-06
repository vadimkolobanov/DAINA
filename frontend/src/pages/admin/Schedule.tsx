import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getSchedule, updateScheduleDay, ScheduleDay } from "../../api/client";

const DAY_NAMES = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"];

export default function Schedule() {
  const [schedule, setSchedule] = useState<ScheduleDay[]>([]);
  const [editing, setEditing] = useState<number | null>(null);
  const [editStart, setEditStart] = useState("");
  const [editEnd, setEditEnd] = useState("");
  const [editError, setEditError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    getSchedule().then(setSchedule);
  }, []);

  const toggleDay = async (day: ScheduleDay) => {
    const updated = { ...day, is_working: !day.is_working };
    await updateScheduleDay(updated);
    setSchedule((prev) =>
      prev.map((d) => (d.day_of_week === day.day_of_week ? { ...d, is_working: !d.is_working } : d))
    );
  };

  const saveEdit = async (day: ScheduleDay) => {
    if (!editStart || !editEnd || editStart >= editEnd) {
      setEditError("Начало должно быть раньше конца");
      return;
    }
    setEditError("");
    try {
      const updated = { ...day, time_start: editStart, time_end: editEnd };
      await updateScheduleDay(updated);
      setSchedule((prev) =>
        prev.map((d) =>
          d.day_of_week === day.day_of_week ? { ...d, time_start: editStart, time_end: editEnd } : d
        )
      );
      setEditing(null);
    } catch {
      setEditError("Не удалось сохранить");
    }
  };

  return (
    <div>
      <h1 className="page-title">Расписание</h1>
      <p className="page-subtitle">Нажмите на день для редактирования</p>

      {schedule.map((day, i) => (
        <motion.div
          key={day.day_of_week}
          className="dashboard-card"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05 }}
          style={{ marginBottom: 8 }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <strong>{DAY_NAMES[day.day_of_week]}</strong>
              {day.is_working ? (
                <div style={{ fontSize: 14, color: "var(--tg-theme-hint-color)", marginTop: 4 }}>
                  {day.time_start} — {day.time_end}
                </div>
              ) : (
                <div style={{ fontSize: 14, color: "var(--danger)", marginTop: 4 }}>Выходной</div>
              )}
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                className={`filter-chip ${day.is_working ? "active" : ""}`}
                onClick={() => toggleDay(day)}
                style={{ fontSize: 12 }}
              >
                {day.is_working ? "Раб." : "Вых."}
              </button>
              {day.is_working && (
                <button
                  className="filter-chip"
                  onClick={() => {
                    setEditing(day.day_of_week);
                    setEditStart(day.time_start);
                    setEditEnd(day.time_end);
                  }}
                  style={{ fontSize: 12 }}
                >
                  Изм.
                </button>
              )}
            </div>
          </div>

          {editing === day.day_of_week && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              style={{ marginTop: 12 }}
            >
              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
                <input
                  type="time"
                  className="search-input"
                  value={editStart}
                  onChange={(e) => setEditStart(e.target.value)}
                  style={{ marginBottom: 0, flex: 1 }}
                />
                <span>—</span>
                <input
                  type="time"
                  className="search-input"
                  value={editEnd}
                  onChange={(e) => setEditEnd(e.target.value)}
                  style={{ marginBottom: 0, flex: 1 }}
                />
              </div>
              {editError && (
                <div style={{ fontSize: 13, color: "var(--danger)", marginBottom: 8 }}>{editError}</div>
              )}
              <button className="btn btn--primary" onClick={() => saveEdit(day)}>
                Сохранить
              </button>
            </motion.div>
          )}
        </motion.div>
      ))}

      <div className="tab-nav">
        <button className="tab-nav__item" onClick={() => navigate("/")}>
          <span className="tab-nav__icon">📊</span>
          Главная
        </button>
        <button className="tab-nav__item" onClick={() => navigate("/clients")}>
          <span className="tab-nav__icon">👥</span>
          Клиенты
        </button>
        <button className="tab-nav__item active" onClick={() => navigate("/schedule")}>
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
