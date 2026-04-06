import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getAdminConfig, updateAdminConfig } from "../../api/client";

interface ConfigField {
  key: string;
  label: string;
  hint?: string;
  type?: "text" | "toggle";
}

interface ConfigSection {
  title: string;
  fields: ConfigField[];
}

const CONFIG_SECTIONS: ConfigSection[] = [
  {
    title: "Студия",
    fields: [
      { key: "app_name", label: "Название студии", hint: "Отображается в приветствии бота" },
      { key: "master_name", label: "Имя мастера", hint: "Используется в сообщениях клиентам" },
      { key: "studio_address", label: "Адрес студии", hint: "Показывается в напоминаниях" },
      { key: "studio_map_url", label: "Ссылка на карту", hint: "Яндекс.Карты или Google Maps" },
    ],
  },
  {
    title: "Бот",
    fields: [
      { key: "bot_username", label: "Username бота", hint: "Без @, например: DAINANailBot" },
      { key: "admin_ids", label: "ID администраторов", hint: "Telegram ID через запятую. Узнать свой: @userinfobot" },
    ],
  },
  {
    title: "Расписание",
    fields: [
      { key: "correction_days", label: "Дней до коррекции", hint: "Через сколько дней предложить повторный визит" },
    ],
  },
  {
    title: "Уведомления",
    fields: [
      { key: "reminder_24h", label: "Напоминание за 24 часа", type: "toggle" },
      { key: "reminder_2h", label: "Напоминание за 2 часа", type: "toggle" },
      { key: "followup_enabled", label: "Сообщение после визита", type: "toggle" },
    ],
  },
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

  const toggleValue = (key: string) => {
    if (!config) return;
    const current = config[key];
    setConfig({ ...config, [key]: current === "true" ? "false" : "true" });
  };

  if (error) return <div className="hint">Не удалось загрузить настройки</div>;
  if (!config) return <div className="hint">Загрузка...</div>;

  let fieldIndex = 0;

  return (
    <div>
      <h1 className="page-title">Настройки</h1>

      {CONFIG_SECTIONS.map((section) => (
        <div key={section.title} style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.5, color: "var(--tg-theme-hint-color)", marginBottom: 8, paddingLeft: 4 }}>
            {section.title}
          </div>

          {section.fields.map((field) => {
            const i = fieldIndex++;
            const isToggle = field.type === "toggle";
            const isOn = config[field.key] === "true";

            return (
              <motion.div
                key={field.key}
                className="dashboard-card"
                style={{ marginBottom: 8 }}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.02 }}
              >
                {isToggle ? (
                  <div
                    style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
                    onClick={() => toggleValue(field.key)}
                  >
                    <div>
                      <div style={{ fontSize: 15 }}>{field.label}</div>
                      {field.hint && (
                        <div style={{ fontSize: 12, color: "var(--tg-theme-hint-color)", marginTop: 2 }}>{field.hint}</div>
                      )}
                    </div>
                    <div
                      style={{
                        width: 48,
                        height: 28,
                        borderRadius: 14,
                        background: isOn ? "var(--success)" : "var(--tg-theme-secondary-bg-color)",
                        transition: "background 0.2s",
                        position: "relative",
                        flexShrink: 0,
                        marginLeft: 12,
                      }}
                    >
                      <div
                        style={{
                          width: 22,
                          height: 22,
                          borderRadius: 11,
                          background: "white",
                          position: "absolute",
                          top: 3,
                          left: isOn ? 23 : 3,
                          transition: "left 0.2s",
                          boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
                        }}
                      />
                    </div>
                  </div>
                ) : (
                  <>
                    <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>
                      {field.label}
                    </label>
                    <input
                      className="search-input"
                      style={{ marginBottom: 0 }}
                      value={config[field.key] || ""}
                      onChange={(e) => setConfig({ ...config, [field.key]: e.target.value })}
                      placeholder={field.hint}
                    />
                    {field.hint && (
                      <div style={{ fontSize: 11, color: "var(--tg-theme-hint-color)", marginTop: 4 }}>{field.hint}</div>
                    )}
                  </>
                )}
              </motion.div>
            );
          })}
        </div>
      ))}

      <button
        className="btn btn--primary"
        style={{ marginTop: 8 }}
        onClick={handleSave}
        disabled={saving}
      >
        {saving ? "Сохранение..." : saved ? "Сохранено!" : "Сохранить настройки"}
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
