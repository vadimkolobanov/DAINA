import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getServices, ServiceItem } from "../../api/client";
import { useTelegram } from "../../hooks/useTelegram";
import StepIndicator from "../../components/StepIndicator";
import { BookingState } from "../../App";

interface Props {
  booking: BookingState;
  setBooking: (b: BookingState) => void;
}

export default function ServiceSelect({ booking, setBooking }: Props) {
  const [services, setServices] = useState<ServiceItem[]>([]);
  const { user, haptic } = useTelegram();
  const navigate = useNavigate();

  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getServices()
      .then(setServices)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  const selectService = (s: ServiceItem) => {
    haptic("medium");
    setBooking({
      serviceId: s.id,
      serviceName: s.name,
      servicePrice: s.price,
      serviceDuration: s.duration_minutes,
      date: "",
      time: "",
    });
    navigate("/date");
  };

  return (
    <div>
      <StepIndicator current={0} total={4} />
      <motion.h1
        className="page-title"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        {user ? `${user.first_name}, выберите услугу` : "Выберите услугу"}
      </motion.h1>
      <p className="page-subtitle">Нажмите на карточку, чтобы продолжить</p>

      {error && <div className="hint">Не удалось загрузить услуги. Попробуйте позже.</div>}

      {loading && !error && (
        <div className="skeleton">
          <div className="skeleton__block skeleton__block--lg" />
          <div className="skeleton__block skeleton__block--lg" />
          <div className="skeleton__block skeleton__block--lg" />
        </div>
      )}

      {services.map((s, i) => (
        <motion.div
          key={s.id}
          className={`service-card ${booking.serviceId === s.id ? "selected" : ""}`}
          onClick={() => selectService(s)}
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.1, type: "spring", stiffness: 100 }}
          whileTap={{ scale: 0.98 }}
        >
          <div className="service-card__name">{s.name}</div>
          <div className="service-card__description">{s.description}</div>
          <div className="service-card__meta">
            <span className="service-card__duration">от {s.duration_minutes} мин</span>
            <span className="service-card__price">
              {s.old_price && (
                <span style={{ textDecoration: "line-through", opacity: 0.5, marginRight: 6, fontSize: 14 }}>
                  {s.old_price} руб
                </span>
              )}
              {s.price} руб
            </span>
          </div>
        </motion.div>
      ))}

      <div style={{ display: "flex", gap: 8, marginTop: 20 }}>
        <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => navigate("/my-bookings")}>
          📋 Мои записи
        </button>
        <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => navigate("/gallery")}>
          🖼 Галерея
        </button>
        <button className="btn btn--secondary" style={{ flex: 1 }} onClick={() => navigate("/contacts")}>
          📞 Контакты
        </button>
      </div>
    </div>
  );
}
