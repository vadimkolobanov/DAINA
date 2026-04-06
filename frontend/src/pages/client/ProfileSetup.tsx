import { useState } from "react";
import { motion } from "framer-motion";
import { updateClient } from "../../api/client";

interface Props {
  clientId: number;
  existingPhone: string | null;
  existingInstagram: string | null;
  onComplete: () => void;
}

export default function ProfileSetup({ clientId, existingPhone, existingInstagram, onComplete }: Props) {
  const [phone, setPhone] = useState(existingPhone || "");
  const [instagram, setInstagram] = useState(existingInstagram || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    const cleaned = phone.replace(/\s/g, "");
    if (!cleaned || cleaned.length < 7) {
      setError("Введите корректный номер телефона");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await updateClient(clientId, {
        phone: cleaned,
        instagram_handle: instagram.replace("@", "").trim() || null,
      });
      onComplete();
    } catch {
      setError("Не удалось сохранить. Попробуйте ещё раз.");
      setSaving(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ padding: "20px 0" }}
    >
      <div style={{ textAlign: "center", marginBottom: 24 }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>💅</div>
        <h1 className="page-title" style={{ marginBottom: 8 }}>Добро пожаловать!</h1>
        <p className="page-subtitle" style={{ marginBottom: 0 }}>
          Для записи нам нужен ваш номер телефона — на случай если нужно будет связаться
        </p>
      </div>

      <div className="dashboard-card">
        <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>
          Номер телефона *
        </label>
        <input
          className="search-input"
          type="tel"
          placeholder="+375 29 123 45 67"
          value={phone}
          onChange={(e) => setPhone(e.target.value)}
          style={{ marginBottom: 16 }}
        />

        <label style={{ fontSize: 13, color: "var(--tg-theme-hint-color)", display: "block", marginBottom: 4 }}>
          Instagram (необязательно)
        </label>
        <input
          className="search-input"
          placeholder="@username"
          value={instagram}
          onChange={(e) => setInstagram(e.target.value)}
          style={{ marginBottom: 0 }}
        />
        <div style={{ fontSize: 11, color: "var(--tg-theme-hint-color)", marginTop: 4 }}>
          Чтобы мастер мог найти вас в Instagram
        </div>
      </div>

      {error && (
        <div className="hint" style={{ color: "var(--danger)" }}>
          {error}
        </div>
      )}

      <button
        className="btn btn--primary"
        style={{ marginTop: 16 }}
        onClick={handleSubmit}
        disabled={saving}
      >
        {saving ? "Сохраняем..." : "Продолжить"}
      </button>
    </motion.div>
  );
}
