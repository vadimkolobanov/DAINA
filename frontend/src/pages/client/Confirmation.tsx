import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import StepIndicator from "../../components/StepIndicator";
import { useTelegram } from "../../hooks/useTelegram";
import { createBooking } from "../../api/client";
import { BookingState } from "../../App";
import { useEffect, useState } from "react";

interface Props {
  booking: BookingState;
}

export default function Confirmation({ booking }: Props) {
  const navigate = useNavigate();
  const { user, hapticSuccess, tg } = useTelegram();
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!booking.time) {
      navigate("/");
    }
    tg?.BackButton?.show();
    const back = () => navigate("/time");
    tg?.BackButton?.onClick(back);
    return () => {
      tg?.BackButton?.offClick(back);
      tg?.BackButton?.hide();
    };
  }, []);

  const dateFormatted = booking.date
    ? new Date(booking.date).toLocaleDateString("ru-RU", {
        weekday: "long",
        day: "numeric",
        month: "long",
      })
    : "";

  const endTime = () => {
    if (!booking.time) return "";
    const [h, m] = booking.time.split(":").map(Number);
    const end = new Date(2000, 0, 1, h, m + booking.serviceDuration);
    return `${String(end.getHours()).padStart(2, "0")}:${String(end.getMinutes()).padStart(2, "0")}`;
  };

  const handleConfirm = async () => {
    if (submitting || !user) return;
    setSubmitting(true);
    try {
      // First get or create the client from the API
      const res = await fetch(`/api/clients/telegram/${user.id}`);
      let clientId: number;
      if (res.ok) {
        const client = await res.json();
        clientId = client.id;
      } else {
        // Client doesn't exist yet in DB — this shouldn't happen if bot /start ran,
        // but handle gracefully
        setSubmitting(false);
        return;
      }

      await createBooking({
        client_id: clientId,
        service_id: booking.serviceId!,
        date: booking.date,
        time: booking.time,
      });
      hapticSuccess();
      navigate("/success");
    } catch {
      setSubmitting(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }}>
      <StepIndicator current={3} total={4} />

      <div className="confirmation">
        <div className="confirmation__icon">💅</div>
        <div className="confirmation__title">Ваша запись</div>

        <div className="confirmation__row">
          <span className="confirmation__label">Услуга</span>
          <span className="confirmation__value">{booking.serviceName}</span>
        </div>
        <div className="confirmation__row">
          <span className="confirmation__label">Дата</span>
          <span className="confirmation__value">{dateFormatted}</span>
        </div>
        <div className="confirmation__row">
          <span className="confirmation__label">Время</span>
          <span className="confirmation__value">
            {booking.time} — {endTime()}
          </span>
        </div>
        <div className="confirmation__row">
          <span className="confirmation__label">Стоимость</span>
          <span className="confirmation__value">
            {booking.servicePrice.toLocaleString()}₽
          </span>
        </div>

        <div style={{ marginTop: 24 }}>
          <button
            className="btn btn--primary"
            onClick={handleConfirm}
            disabled={submitting}
          >
            {submitting ? "Записываем..." : "Подтвердить запись"}
          </button>
        </div>

        <button
          className="btn btn--danger"
          style={{ marginTop: 12 }}
          onClick={() => navigate("/")}
        >
          Отменить
        </button>
      </div>
    </motion.div>
  );
}
