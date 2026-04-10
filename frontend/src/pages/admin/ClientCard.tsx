import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { getPublicConfig, getClientDetail, updateClient, updateBookingStatus, deleteBooking, deleteClientApi } from "../../api/client";

interface BookingItem {
  id: number;
  service_name: string;
  date: string;
  time_start: string;
  time_end: string;
  status: string;
  price: number;
}

interface ClientDetail {
  id: number;
  telegram_id: number;
  first_name: string;
  last_name: string | null;
  username: string | null;
  phone: string | null;
  instagram_handle: string | null;
  notes: string | null;
  is_vip: boolean;
  visit_count: number;
  total_spent: number;
  referral_code: string | null;
  created_at: string | null;
  last_visit_at: string | null;
  bookings: BookingItem[];
  average_check: number;
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

export default function ClientCard() {
  const { clientId } = useParams();
  const [client, setClient] = useState<ClientDetail | null>(null);
  const [editingNotes, setEditingNotes] = useState(false);
  const [notes, setNotes] = useState("");
  const [isVip, setIsVip] = useState(false);
  const [confirmDeleteClient, setConfirmDeleteClient] = useState(false);
  const [confirmStatus, setConfirmStatus] = useState<{bookingId: number; status: string; label: string} | null>(null);
  const [botUsername, setBotUsername] = useState("DAINANailBot");
  const [copied, setCopied] = useState(false);
  const navigate = useNavigate();

  const [error, setError] = useState(false);

  const loadClient = () => {
    getClientDetail(Number(clientId))
      .then((data) => {
        setClient(data);
        setNotes(data.notes || "");
        setIsVip(data.is_vip);
      })
      .catch(() => setError(true));
  };

  useEffect(loadClient, [clientId]);

  useEffect(() => {
    getPublicConfig()
      .then((cfg) => { if (cfg.bot_username) setBotUsername(cfg.bot_username); })
      .catch(() => {});
  }, []);

  const saveNotes = async () => {
    try {
      await updateClient(Number(clientId), { notes });
      setEditingNotes(false);
      setClient((c) => (c ? { ...c, notes } : c));
    } catch { /* keep editing state on error */ }
  };

  const toggleVip = async () => {
    const newVip = !isVip;
    try {
      await updateClient(Number(clientId), { is_vip: newVip });
      setIsVip(newVip);
      setClient((c) => (c ? { ...c, is_vip: newVip } : c));
    } catch { /* revert on error — state unchanged */ }
  };

  const askStatus = (bookingId: number, status: string, label: string) => {
    setConfirmStatus({ bookingId, status, label });
  };

  const doChangeStatus = async () => {
    if (!confirmStatus) return;
    try {
      await updateBookingStatus(confirmStatus.bookingId, confirmStatus.status);
      loadClient();
    } catch { /* status unchanged on error */ }
    setConfirmStatus(null);
  };

  const handleDeleteBooking = async (bookingId: number) => {
    try {
      await deleteBooking(bookingId);
      loadClient();
    } catch { /* booking not deleted on error */ }
  };

  const deleteClient = async () => {
    try {
      await deleteClientApi(Number(clientId));
      navigate("/clients");
    } catch {
      // stay on page
    }
  };

  if (error) return <div className="hint">Не удалось загрузить данные клиента</div>;
  if (!client) return <div className="hint">Загрузка...</div>;

  const fullName = `${client.first_name} ${client.last_name || ""}`.trim();

  return (
    <div>
      {/* Header */}
      <motion.div
        className="dashboard-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ textAlign: "center", paddingTop: 24, paddingBottom: 24 }}
      >
        <div className="client-item__avatar" style={{ width: 64, height: 64, fontSize: 28, margin: "0 auto 12px" }}>
          {client.first_name.charAt(0).toUpperCase()}
        </div>
        <h2 style={{ fontSize: 22, marginBottom: 4 }}>{fullName}</h2>

        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 12, alignItems: "center" }}>
          {client.phone && (
            <button
              onClick={() => {
                navigator.clipboard.writeText(client.phone!);
                const tg = window.Telegram?.WebApp;
                if (tg?.showAlert) tg.showAlert(`Скопировано: ${client.phone}`);
              }}
              style={{ fontSize: 15, color: "var(--accent-dark)", fontWeight: 500, background: "none", border: "none", cursor: "pointer", padding: 0 }}
            >
              📞 {client.phone}
            </button>
          )}
          {client.instagram_handle && (
            <button
              onClick={() => {
                const tg = window.Telegram?.WebApp;
                if (tg?.openLink) tg.openLink(`https://instagram.com/${client.instagram_handle}`);
                else window.open(`https://instagram.com/${client.instagram_handle}`, "_blank");
              }}
              style={{ fontSize: 15, color: "var(--accent-dark)", fontWeight: 500, background: "none", border: "none", cursor: "pointer", padding: 0 }}
            >
              📷 @{client.instagram_handle}
            </button>
          )}
          {client.username && (
            <button
              onClick={() => {
                const tg = window.Telegram?.WebApp;
                if (tg?.openTelegramLink) tg.openTelegramLink(`https://t.me/${(client.username || "").replace("@", "")}`);
                else window.open(`https://t.me/${client.username}`, "_blank");
              }}
              style={{ fontSize: 15, color: "var(--accent-dark)", fontWeight: 500, background: "none", border: "none", cursor: "pointer", padding: 0 }}
            >
              ✈️ @{client.username}
            </button>
          )}
        </div>

        <div style={{ marginTop: 12, display: "flex", justifyContent: "center", gap: 8 }}>
          <button
            className={`filter-chip ${isVip ? "active" : ""}`}
            onClick={toggleVip}
          >
            {isVip ? "VIP" : "Сделать VIP"}
          </button>
        </div>
      </motion.div>

      {/* Stats */}
      <div className="stat-grid">
        <motion.div className="stat-card" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}>
          <div className="stat-card__value">{client.visit_count}</div>
          <div className="stat-card__label">Визитов</div>
        </motion.div>
        <motion.div className="stat-card" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.05 }}>
          <div className="stat-card__value">{client.total_spent.toLocaleString()} руб</div>
          <div className="stat-card__label">Всего</div>
        </motion.div>
        <motion.div className="stat-card" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.1 }}>
          <div className="stat-card__value">{client.average_check.toLocaleString()} руб</div>
          <div className="stat-card__label">Средний чек</div>
        </motion.div>
        <motion.div className="stat-card" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.15 }}>
          <div className="stat-card__value">
            {client.last_visit_at
              ? new Date(client.last_visit_at).toLocaleDateString("ru-RU", { day: "numeric", month: "short" })
              : "—"}
          </div>
          <div className="stat-card__label">Посл. визит</div>
        </motion.div>
      </div>

      {/* Notes */}
      <motion.div
        className="dashboard-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <div className="dashboard-card__header" style={{ display: "flex", justifyContent: "space-between" }}>
          <span>Заметки</span>
          <button
            className="filter-chip"
            style={{ fontSize: 11, padding: "2px 10px" }}
            onClick={() => editingNotes ? saveNotes() : setEditingNotes(true)}
          >
            {editingNotes ? "Сохранить" : "Изменить"}
          </button>
        </div>
        {editingNotes ? (
          <textarea
            className="search-input"
            style={{ minHeight: 80, marginBottom: 0, resize: "vertical" }}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Предпочтения, аллергии, особенности..."
          />
        ) : (
          <div style={{ fontSize: 14, color: notes ? "var(--tg-theme-text-color)" : "var(--tg-theme-hint-color)", lineHeight: 1.5 }}>
            {notes || "Нет заметок"}
          </div>
        )}
      </motion.div>

      {/* Booking history */}
      <motion.div
        className="dashboard-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <div className="dashboard-card__header">
          История записей ({client.bookings.length})
        </div>

        {client.bookings.length === 0 && (
          <div style={{ fontSize: 14, color: "var(--tg-theme-hint-color)", padding: "8px 0" }}>
            Нет записей
          </div>
        )}

        {client.bookings.map((b) => (
          <div key={b.id} style={{ borderBottom: "1px solid var(--tg-theme-secondary-bg-color)", paddingBottom: 12, marginBottom: 12 }}>
            <div className="booking-item" style={{ borderBottom: "none", paddingBottom: 0 }}>
              <div style={{ minWidth: 36, textAlign: "center", fontSize: 18 }}>
                {statusEmoji[b.status] || "❓"}
              </div>
              <div className="booking-item__info">
                <div className="booking-item__name">{b.service_name}</div>
                <div className="booking-item__service">
                  {new Date(b.date).toLocaleDateString("ru-RU", {
                    day: "numeric",
                    month: "short",
                    weekday: "short",
                  })}{" "}
                  &bull; {b.time_start}–{b.time_end}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{b.price.toLocaleString()} руб</div>
                <div style={{ fontSize: 11, color: "var(--tg-theme-hint-color)" }}>
                  {statusLabel[b.status]}
                </div>
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ display: "flex", gap: 6, marginTop: 8, marginLeft: 36, flexWrap: "wrap" }}>
              {b.status === "pending" && (
                <>
                  <button className="filter-chip active" style={{ fontSize: 11, padding: "4px 10px" }} onClick={() => askStatus(b.id, "confirmed", "Подтвердить")}>
                    Подтвердить
                  </button>
                  <button className="filter-chip" style={{ fontSize: 11, padding: "4px 10px" }} onClick={() => askStatus(b.id, "cancelled", "Отклонить")}>
                    Отклонить
                  </button>
                </>
              )}
              {b.status === "confirmed" && (
                <>
                  <button className="filter-chip active" style={{ fontSize: 11, padding: "4px 10px" }} onClick={() => askStatus(b.id, "completed", "Завершить")}>
                    Завершить
                  </button>
                  <button className="filter-chip" style={{ fontSize: 11, padding: "4px 10px" }} onClick={() => askStatus(b.id, "no_show", "Не пришёл")}>
                    Не пришёл
                  </button>
                  <button className="filter-chip" style={{ fontSize: 11, padding: "4px 10px" }} onClick={() => askStatus(b.id, "cancelled", "Отменить")}>
                    Отменить
                  </button>
                </>
              )}
              <button
                className="filter-chip"
                style={{ fontSize: 11, padding: "4px 10px", color: "var(--danger)" }}
                onClick={() => handleDeleteBooking(b.id)}
              >
                Удалить
              </button>
            </div>
          </div>
        ))}
      </motion.div>

      {/* Status confirmation modal */}
      {confirmStatus && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          style={{
            position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
            background: "rgba(0,0,0,0.4)", zIndex: 200,
            display: "flex", alignItems: "center", justifyContent: "center", padding: 24,
          }}
          onClick={() => setConfirmStatus(null)}
        >
          <motion.div
            className="dashboard-card"
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            style={{ textAlign: "center", maxWidth: 300, width: "100%" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>
              {confirmStatus.label}?
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => setConfirmStatus(null)}>
                Отмена
              </button>
              <button className="btn btn--primary" style={{ flex: 1 }} onClick={doChangeStatus}>
                Да
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* Deeplink */}
      {client.referral_code && (
        <motion.div
          className="dashboard-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="dashboard-card__header">Ссылка для клиента</div>
          <div
            style={{
              fontSize: 13,
              background: "var(--tg-theme-secondary-bg-color)",
              padding: "10px 12px",
              borderRadius: 8,
              wordBreak: "break-all",
              cursor: "pointer",
            }}
            onClick={() => {
              navigator.clipboard.writeText(`t.me/${botUsername}?start=ref_${client.referral_code}`);
              setCopied(true);
              setTimeout(() => setCopied(false), 2000);
            }}
          >
            t.me/${botUsername}?start=ref_{client.referral_code}
            <div style={{ fontSize: 11, color: copied ? "var(--success)" : "var(--tg-theme-hint-color)", marginTop: 4 }}>
              {copied ? "Скопировано!" : "Нажмите чтобы скопировать"}
            </div>
          </div>
        </motion.div>
      )}

      {/* Delete client */}
      <motion.div
        className="dashboard-card"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        style={{ marginTop: 16 }}
      >
        {!confirmDeleteClient ? (
          <button
            className="btn btn--danger"
            onClick={() => setConfirmDeleteClient(true)}
          >
            Удалить клиента
          </button>
        ) : (
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 14, marginBottom: 12, color: "var(--danger)" }}>
              Удалить клиента и все его записи? Это нельзя отменить.
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => setConfirmDeleteClient(false)}>
                Отмена
              </button>
              <button
                className="btn btn--primary"
                style={{ flex: 1, background: "var(--danger)" }}
                onClick={deleteClient}
              >
                Да, удалить
              </button>
            </div>
          </div>
        )}
      </motion.div>

      {/* Back button */}
      <button
        className="btn btn--secondary"
        style={{ marginTop: 12 }}
        onClick={() => navigate(-1)}
      >
        Назад
      </button>

      <div className="tab-nav">
        <button className="tab-nav__item" onClick={() => navigate("/")}>
          <span className="tab-nav__icon">📊</span>
          Главная
        </button>
        <button className="tab-nav__item" onClick={() => navigate("/all-bookings")}>
          <span className="tab-nav__icon">📋</span>
          Записи
        </button>
        <button className="tab-nav__item active" onClick={() => navigate("/clients")}>
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
