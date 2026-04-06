import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getAdminConfig, updateAdminConfig } from "../../api/client";

const CONFIG_LABELS: Record<string, string> = {
  admin_ids: "ID администраторов (через запятую)",
  bot_username: "Username бота (без @)",
  app_name: "Название студии",
  master_name: "Имя мастера",
  studio_address: "Адрес студии",
  studio_map_url: "Ссылка на карту",
  correction_days: "Дней до коррекции",
  reminder_24h: "Напоминание за 24 часа (true/false)",
  reminder_2h: "Напоминание за 2 часа (true/false)",
  followup_enabled: "Follow-up после визита (true/false)",
};

const CONFIG_ORDER = [
  "app_name",
  "master_name",
  "bot_username",
  "admin_ids",
  "studio_address",
  "studio_map_url",
  "correction_days",
  "reminder_24h",
  "reminder_2h",
  "followup_enabled",
];

export default function Settings() {
  const [config, setConfig] = useState<Record<string, string> | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    getAdminConfig()
      .then(setConfig)
      .catch(() => setError(true));
  }, []);

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    setSaved(false);
    try {
      await updateAdminConfig(config);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      setError(true);
    }
    setSaving(false);
  };

  if (error) return <div className="hint">Не удалось загрузить настройки</div>;
  if (!config) return <div className="hint">Загрузка...</div>;

  return (
    <div>
      <h1 className="page-title">Настройки</h1>

      {CONFIG_ORDER.map((key, i) => (
        <motion.div
          key={key}
          className="dashboard-card"
          style={{ marginBottom: 8 }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.03 }}
        >
          <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>
            {CONFIG_LABELS[key] || key}
          </label>
          <input
            className="search-input"
            style={{ marginBottom: 0 }}
            value={config[key] || ""}
            onChange={(e) => setConfig({ ...config, [key]: e.target.value })}
          />
        </motion.div>
      ))}

      <button
        className="btn btn--primary"
        style={{ marginTop: 16 }}
        onClick={handleSave}
        disabled={saving}
      >
        {saving ? "Сохранение..." : saved ? "Сохранено!" : "Сохранить настройки"}
      </button>

      <button
        className="btn btn--secondary"
        style={{ marginTop: 8 }}
        onClick={() => navigate("/")}
      >
        Назад
      </button>

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
        <button className="tab-nav__item" onClick={() => navigate("/stats")}>
          <span className="tab-nav__icon">📈</span>
          Стат-ка
        </button>
      </div>
    </div>
  );
}
