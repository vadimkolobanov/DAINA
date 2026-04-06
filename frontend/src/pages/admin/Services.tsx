import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  getAllServices,
  createService,
  updateService,
  deleteService,
  getPublicConfig,
  ServiceItem,
} from "../../api/client";

interface EditingService {
  id: number | null; // null = new
  name: string;
  description: string;
  duration_minutes: string;
  price: string;
  old_price: string;
  is_active: boolean;
  sort_order: string;
}

const empty: EditingService = {
  id: null,
  name: "",
  description: "",
  duration_minutes: "60",
  price: "",
  old_price: "",
  is_active: true,
  sort_order: "0",
};

export default function Services() {
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [editing, setEditing] = useState<EditingService | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [currency, setCurrency] = useState("руб");
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const navigate = useNavigate();

  const load = () => {
    getAllServices().then(setServices).catch(() => {});
  };

  useEffect(() => {
    load();
    getPublicConfig()
      .then((c) => setCurrency(c.currency || "руб"))
      .catch(() => {});
  }, []);

  const startEdit = (s: ServiceItem) => {
    setEditing({
      id: s.id,
      name: s.name,
      description: s.description || "",
      duration_minutes: String(s.duration_minutes),
      price: String(s.price),
      old_price: s.old_price ? String(s.old_price) : "",
      is_active: s.is_active,
      sort_order: String(s.sort_order),
    });
    setError("");
  };

  const handleSave = async () => {
    if (!editing) return;
    if (!editing.name || !editing.price || !editing.duration_minutes) {
      setError("Заполните название, цену и длительность");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const data = {
        name: editing.name,
        description: editing.description || null,
        duration_minutes: parseInt(editing.duration_minutes),
        price: parseInt(editing.price),
        old_price: editing.old_price ? parseInt(editing.old_price) : null,
        is_active: editing.is_active,
        sort_order: parseInt(editing.sort_order) || 0,
      };
      if (editing.id) {
        await updateService(editing.id, data);
      } else {
        await createService(data);
      }
      setEditing(null);
      load();
    } catch {
      setError("Не удалось сохранить");
    }
    setSaving(false);
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteService(id);
      setConfirmDeleteId(null);
      load();
    } catch {
      setError("Не удалось удалить");
    }
  };

  return (
    <div>
      <h1 className="page-title">Услуги</h1>

      {editing ? (
        <motion.div
          className="dashboard-card"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="dashboard-card__header">
            {editing.id ? "Редактирование" : "Новая услуга"}
          </div>

          <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>
            Название *
          </label>
          <input
            className="search-input"
            value={editing.name}
            onChange={(e) => setEditing({ ...editing, name: e.target.value })}
          />

          <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>
            Описание
          </label>
          <textarea
            className="search-input"
            style={{ minHeight: 80, resize: "vertical", lineHeight: 1.5 }}
            value={editing.description}
            onChange={(e) => setEditing({ ...editing, description: e.target.value })}
          />

          <div style={{ display: "flex", gap: 8 }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>
                Цена ({currency}) *
              </label>
              <input
                className="search-input"
                type="number"
                value={editing.price}
                onChange={(e) => setEditing({ ...editing, price: e.target.value })}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>
                Старая цена (скидка)
              </label>
              <input
                className="search-input"
                type="number"
                value={editing.old_price}
                onChange={(e) => setEditing({ ...editing, old_price: e.target.value })}
                placeholder="Пусто = без скидки"
              />
            </div>
          </div>

          <div style={{ display: "flex", gap: 8 }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>
                Длительность (мин) *
              </label>
              <input
                className="search-input"
                type="number"
                value={editing.duration_minutes}
                onChange={(e) => setEditing({ ...editing, duration_minutes: e.target.value })}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>
                Порядок
              </label>
              <input
                className="search-input"
                type="number"
                value={editing.sort_order}
                onChange={(e) => setEditing({ ...editing, sort_order: e.target.value })}
              />
            </div>
          </div>

          <div
            style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16, cursor: "pointer" }}
            onClick={() => setEditing({ ...editing, is_active: !editing.is_active })}
          >
            <div
              style={{
                width: 48, height: 28, borderRadius: 14,
                background: editing.is_active ? "var(--success)" : "var(--tg-theme-secondary-bg-color)",
                position: "relative", transition: "background 0.2s",
              }}
            >
              <div style={{
                width: 22, height: 22, borderRadius: 11, background: "white",
                position: "absolute", top: 3, left: editing.is_active ? 23 : 3,
                transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
              }} />
            </div>
            <span style={{ fontSize: 14 }}>
              {editing.is_active ? "Активна" : "Скрыта"}
            </span>
          </div>

          {error && <div className="hint" style={{ color: "var(--danger)" }}>{error}</div>}

          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => setEditing(null)}>
              Отмена
            </button>
            <button className="btn btn--primary" style={{ flex: 1 }} onClick={handleSave} disabled={saving}>
              {saving ? "Сохранение..." : "Сохранить"}
            </button>
          </div>
        </motion.div>
      ) : (
        <>
          {services.map((s, i) => (
            <motion.div
              key={s.id}
              className="dashboard-card"
              style={{ marginBottom: 8, opacity: s.is_active ? 1 : 0.5 }}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: s.is_active ? 1 : 0.5, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => startEdit(s)}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
                    {s.name}
                    {!s.is_active && <span style={{ fontSize: 11, color: "var(--tg-theme-hint-color)", marginLeft: 8 }}>скрыта</span>}
                  </div>
                  <div style={{ fontSize: 13, color: "var(--tg-theme-hint-color)" }}>
                    от {s.duration_minutes} мин
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  {s.old_price && (
                    <div style={{ fontSize: 13, textDecoration: "line-through", color: "var(--tg-theme-hint-color)" }}>
                      {s.old_price} {currency}
                    </div>
                  )}
                  <div style={{ fontSize: 18, fontWeight: 700, color: "var(--accent-dark)" }}>
                    {s.price} {currency}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}

          {services.length === 0 && <div className="hint">Нет услуг</div>}

          <button
            className="btn btn--primary"
            style={{ marginTop: 16 }}
            onClick={() => { setEditing({ ...empty }); setError(""); }}
          >
            + Добавить услугу
          </button>
        </>
      )}

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
