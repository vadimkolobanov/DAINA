import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  getSlotsByDate,
  getSlotDates,
  getServices,
  createSlot,
  createSlotsBatch,
  deleteSlot,
  manualBookSlot,
  manualUnbookSlot,
  SlotItem,
  SlotDateSummary,
  ServiceItem,
  SlotCreate,
} from "../../api/client";

const MONTH_NAMES = [
  "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
];
const WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

function pad(n: number) {
  return n.toString().padStart(2, "0");
}

function formatDate(d: Date) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

function addMinutes(timeStr: string, minutes: number): string {
  const [h, m] = timeStr.split(":").map(Number);
  const total = Math.min(h * 60 + m + minutes, 23 * 60 + 59);
  return `${pad(Math.floor(total / 60))}:${pad(total % 60)}`;
}

export default function Slots() {
  const navigate = useNavigate();
  const today = new Date();
  const [currentMonth, setCurrentMonth] = useState(today.getMonth());
  const [currentYear, setCurrentYear] = useState(today.getFullYear());
  const [selectedDate, setSelectedDate] = useState<string>(formatDate(today));
  const [slots, setSlots] = useState<SlotItem[]>([]);
  const [dateSummary, setDateSummary] = useState<SlotDateSummary[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [loading, setLoading] = useState(false);

  // Add slot form
  const [showAdd, setShowAdd] = useState(false);
  const [addServiceId, setAddServiceId] = useState<number>(0);
  const [addTime, setAddTime] = useState("18:00");
  const [addDuration, setAddDuration] = useState(60);
  const [addCount, setAddCount] = useState(1);
  const [addRepeat, setAddRepeat] = useState<"none" | "weekdays" | "weekends" | "daily">("none");
  const [addRepeatDays, setAddRepeatDays] = useState(7);
  const [addLoading, setAddLoading] = useState(false);

  // Manual book form
  const [manualBookId, setManualBookId] = useState<number | null>(null);
  const [manualName, setManualName] = useState("");
  const [manualNote, setManualNote] = useState("");

  useEffect(() => {
    getServices().then((s) => {
      setServices(s);
      if (s.length > 0 && addServiceId === 0) setAddServiceId(s[0].id);
    });
  }, []);

  useEffect(() => {
    loadDateSummary();
  }, [currentMonth, currentYear]);

  useEffect(() => {
    if (selectedDate) loadSlots();
  }, [selectedDate]);

  const loadDateSummary = async () => {
    const start = `${currentYear}-${pad(currentMonth + 1)}-01`;
    const lastDay = new Date(currentYear, currentMonth + 1, 0).getDate();
    const end = `${currentYear}-${pad(currentMonth + 1)}-${pad(lastDay)}`;
    try {
      const data = await getSlotDates(start, end);
      setDateSummary(data);
    } catch {}
  };

  const loadSlots = async () => {
    setLoading(true);
    try {
      const data = await getSlotsByDate(selectedDate);
      setSlots(data);
    } catch {}
    setLoading(false);
  };

  const handleAddSlot = async () => {
    if (!addServiceId || !addTime || addDuration < 5 || addLoading) return;

    // Validate total time doesn't exceed 23:59
    const [startH, startM] = addTime.split(":").map(Number);
    const totalEnd = startH * 60 + startM + addDuration * addCount;
    if (totalEnd > 24 * 60) {
      alert("Окошки выходят за пределы суток. Уменьшите количество или длительность.");
      return;
    }

    setAddLoading(true);

    // Build list of dates
    const dates: string[] = [];
    if (addRepeat === "none") {
      dates.push(selectedDate);
    } else {
      const base = new Date(selectedDate + "T12:00:00");
      for (let d = 0; d < addRepeatDays; d++) {
        const dt = new Date(base);
        dt.setDate(base.getDate() + d);
        const dow = dt.getDay(); // 0=Sun, 6=Sat
        if (addRepeat === "weekends" && dow !== 0 && dow !== 6) continue;
        if (addRepeat === "weekdays" && (dow === 0 || dow === 6)) continue;
        dates.push(formatDate(dt));
      }
    }

    if (dates.length === 0) {
      alert("Нет подходящих дат для выбранного режима повторения.");
      setAddLoading(false);
      return;
    }

    // Build slots for each date
    const slotsToCreate: SlotCreate[] = [];
    for (const date of dates) {
      let currentTime = addTime;
      for (let i = 0; i < addCount; i++) {
        const endTime = addMinutes(currentTime, addDuration);
        slotsToCreate.push({
          service_id: addServiceId,
          date,
          time_start: currentTime,
          time_end: endTime,
        });
        currentTime = endTime;
      }
    }

    try {
      if (slotsToCreate.length === 1) {
        await createSlot(slotsToCreate[0]);
      } else {
        await createSlotsBatch(slotsToCreate);
      }
      setShowAdd(false);
      loadSlots();
      loadDateSummary();
    } catch {
      alert("Не удалось создать окошки. Возможно, некоторые уже существуют.");
    }
    setAddLoading(false);
  };

  const handleDelete = async (slotId: number) => {
    try {
      await deleteSlot(slotId);
      loadSlots();
      loadDateSummary();
    } catch {
      alert("Не удалось удалить окошко");
    }
  };

  const handleManualBook = async () => {
    if (!manualBookId || !manualName.trim()) return;
    try {
      await manualBookSlot(manualBookId, manualName.trim(), manualNote.trim() || undefined);
      setManualBookId(null);
      setManualName("");
      setManualNote("");
      loadSlots();
      loadDateSummary();
    } catch {
      alert("Не удалось занять окошко");
    }
  };

  const handleManualUnbook = async (slotId: number) => {
    try {
      await manualUnbookSlot(slotId);
      loadSlots();
      loadDateSummary();
    } catch {
      alert("Не удалось освободить окошко");
    }
  };

  // Calendar rendering
  const firstDay = new Date(currentYear, currentMonth, 1);
  const lastDate = new Date(currentYear, currentMonth + 1, 0).getDate();
  const startWeekday = (firstDay.getDay() + 6) % 7; // Monday=0
  const summaryMap: Record<string, SlotDateSummary> = {};
  dateSummary.forEach((d) => (summaryMap[d.date] = d));

  const prevMonth = () => {
    if (currentMonth === 0) { setCurrentMonth(11); setCurrentYear(currentYear - 1); }
    else setCurrentMonth(currentMonth - 1);
  };
  const nextMonth = () => {
    if (currentMonth === 11) { setCurrentMonth(0); setCurrentYear(currentYear + 1); }
    else setCurrentMonth(currentMonth + 1);
  };

  return (
    <div>
      <h1 className="page-title">Окошки</h1>
      <p className="page-subtitle">Управление доступными записями</p>

      {/* Calendar */}
      <div className="calendar" style={{ marginBottom: 16 }}>
        <div className="calendar__header">
          <button className="calendar__nav" onClick={prevMonth}>&lsaquo;</button>
          <span className="calendar__month">
            {MONTH_NAMES[currentMonth]} {currentYear}
          </span>
          <button className="calendar__nav" onClick={nextMonth}>&rsaquo;</button>
        </div>
        <div className="calendar__weekdays">
          {WEEKDAYS.map((d) => (
            <div key={d} className="calendar__weekday">{d}</div>
          ))}
        </div>
        <div className="calendar__days">
          {Array.from({ length: startWeekday }).map((_, i) => (
            <div key={`e-${i}`} />
          ))}
          {Array.from({ length: lastDate }).map((_, i) => {
            const day = i + 1;
            const dateStr = `${currentYear}-${pad(currentMonth + 1)}-${pad(day)}`;
            const summary = summaryMap[dateStr];
            const hasSlots = summary && summary.total > 0;
            const isSelected = dateStr === selectedDate;
            const isToday = dateStr === formatDate(today);

            return (
              <button
                key={day}
                className={[
                  "calendar__day",
                  isSelected && "calendar__day--selected",
                  isToday && "calendar__day--today",
                  hasSlots && !isSelected && "calendar__day--available",
                ].filter(Boolean).join(" ")}
                onClick={() => setSelectedDate(dateStr)}
              >
                {day}
                {hasSlots && !isSelected && (
                  <span style={{
                    position: "absolute",
                    bottom: 2,
                    fontSize: 8,
                    color: "var(--accent)",
                  }}>
                    {summary.available}/{summary.total}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected date header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600 }}>
          {new Date(selectedDate + "T12:00:00").toLocaleDateString("ru-RU", {
            weekday: "short",
            day: "numeric",
            month: "long",
          })}
        </h2>
        <button
          className="filter-chip active"
          onClick={() => setShowAdd(!showAdd)}
        >
          {showAdd ? "Отмена" : "+ Добавить"}
        </button>
      </div>

      {/* Add slot form */}
      {showAdd && (
        <motion.div
          className="dashboard-card"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          style={{ marginBottom: 12 }}
        >
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>Услуга</label>
            <select
              className="search-input"
              value={addServiceId}
              onChange={(e) => setAddServiceId(Number(e.target.value))}
              style={{ marginBottom: 0 }}
            >
              {services.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
          <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>Время начала</label>
              <input
                type="time"
                className="search-input"
                value={addTime}
                onChange={(e) => setAddTime(e.target.value)}
                style={{ marginBottom: 0 }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>Длительность (мин)</label>
              <input
                type="number"
                className="search-input"
                value={addDuration}
                min={5}
                max={480}
                onChange={(e) => setAddDuration(Number(e.target.value) || 0)}
                style={{ marginBottom: 0 }}
              />
            </div>
            <div style={{ width: 70 }}>
              <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>Кол-во</label>
              <input
                type="number"
                className="search-input"
                value={addCount}
                min={1}
                max={10}
                onChange={(e) => setAddCount(Math.max(1, Math.min(10, Number(e.target.value))))}
                style={{ marginBottom: 0 }}
              />
            </div>
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>Повторить</label>
            <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {([
                ["none", "Только этот день"],
                ["daily", "Каждый день"],
                ["weekdays", "Будни (Пн-Пт)"],
                ["weekends", "Выходные (Сб-Вс)"],
              ] as const).map(([val, label]) => (
                <button
                  key={val}
                  className={`filter-chip ${addRepeat === val ? "active" : ""}`}
                  style={{ fontSize: 12, padding: "5px 10px" }}
                  onClick={() => setAddRepeat(val)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          {addRepeat !== "none" && (
            <div style={{ marginBottom: 10 }}>
              <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>
                На сколько дней вперёд
              </label>
              <div style={{ display: "flex", gap: 6 }}>
                {[7, 14, 30].map((d) => (
                  <button
                    key={d}
                    className={`filter-chip ${addRepeatDays === d ? "active" : ""}`}
                    style={{ fontSize: 12, padding: "5px 10px" }}
                    onClick={() => setAddRepeatDays(d)}
                  >
                    {d} дней
                  </button>
                ))}
              </div>
            </div>
          )}
          <div style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", marginBottom: 10 }}>
            {addCount > 1
              ? `${addCount} окошек: ${addTime} — ${addMinutes(addTime, addDuration * addCount)}`
              : `${addTime} — ${addMinutes(addTime, addDuration)}`
            }
            {addRepeat !== "none" && (
              <span>
                {" "}· {addRepeat === "daily" ? "каждый день" : addRepeat === "weekdays" ? "Пн-Пт" : "Сб-Вс"} на {addRepeatDays} дн.
              </span>
            )}
          </div>
          <button className="btn btn--primary" onClick={handleAddSlot} disabled={addLoading}>
            {addLoading ? "Создаём..." : `Создать ${addCount > 1 ? `${addCount} окошек` : "окошко"}`}
          </button>
        </motion.div>
      )}

      {/* Slots list */}
      {loading ? (
        <div className="skeleton">
          <div className="skeleton__block" />
          <div className="skeleton__block" />
        </div>
      ) : slots.length === 0 ? (
        <div className="hint">Нет окошек на эту дату</div>
      ) : (
        slots.map((slot, i) => (
          <motion.div
            key={slot.id}
            className="dashboard-card"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.03 }}
            style={{ marginBottom: 8 }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  <strong style={{ fontSize: 16, color: "var(--accent-dark)" }}>
                    {slot.time_start} — {slot.time_end}
                  </strong>
                  {slot.is_booked && (
                    <span className={`badge ${slot.is_manual_booking ? "" : "badge--confirmed"}`}
                      style={slot.is_manual_booking ? { background: "var(--warning)", color: "white" } : {}}
                    >
                      {slot.is_manual_booking ? "Ручная" : "Запись"}
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 14, color: "var(--tg-theme-hint-color)" }}>
                  {slot.service_name}
                </div>
                {slot.is_booked && slot.client_name && (
                  <div style={{ fontSize: 14, marginTop: 4, fontWeight: 500 }}>
                    {slot.client_name}
                    {slot.manual_note && (
                      <span style={{ color: "var(--tg-theme-hint-color)", fontWeight: 400 }}>
                        {" "}— {slot.manual_note}
                      </span>
                    )}
                  </div>
                )}
              </div>
              <div style={{ display: "flex", gap: 6, flexShrink: 0, marginLeft: 8 }}>
                {!slot.is_booked && (
                  <>
                    <button
                      className="filter-chip"
                      style={{ fontSize: 12, padding: "6px 10px" }}
                      onClick={() => {
                        setManualBookId(slot.id);
                        setManualName("");
                        setManualNote("");
                      }}
                    >
                      Занять
                    </button>
                    <button
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--danger)",
                        fontSize: 18,
                        cursor: "pointer",
                        padding: "4px 8px",
                      }}
                      onClick={() => handleDelete(slot.id)}
                    >
                      ×
                    </button>
                  </>
                )}
                {slot.is_manual_booking && (
                  <button
                    className="filter-chip"
                    style={{ fontSize: 12, padding: "6px 10px" }}
                    onClick={() => handleManualUnbook(slot.id)}
                  >
                    Освободить
                  </button>
                )}
              </div>
            </div>

            {/* Manual book form inline */}
            {manualBookId === slot.id && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                style={{ marginTop: 10, borderTop: "1px solid var(--tg-theme-secondary-bg-color)", paddingTop: 10 }}
              >
                <input
                  type="text"
                  className="search-input"
                  placeholder="Имя клиента"
                  value={manualName}
                  onChange={(e) => setManualName(e.target.value)}
                  style={{ marginBottom: 8 }}
                  autoFocus
                />
                <input
                  type="text"
                  className="search-input"
                  placeholder="Заметка (необязательно)"
                  value={manualNote}
                  onChange={(e) => setManualNote(e.target.value)}
                  style={{ marginBottom: 8 }}
                />
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn--primary" onClick={handleManualBook} style={{ flex: 1 }}>
                    Занять
                  </button>
                  <button
                    className="btn btn--secondary"
                    onClick={() => setManualBookId(null)}
                    style={{ flex: 1 }}
                  >
                    Отмена
                  </button>
                </div>
              </motion.div>
            )}
          </motion.div>
        ))
      )}

      {/* Bottom nav */}
      <div className="tab-nav">
        <button className="tab-nav__item" onClick={() => navigate("/")}>
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
        <button className="tab-nav__item active" onClick={() => navigate("/slots")}>
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
