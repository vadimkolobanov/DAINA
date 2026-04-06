import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import ConfettiAnimation from "../../components/ConfettiAnimation";
import { useTelegram } from "../../hooks/useTelegram";
import { BookingState } from "../../App";

interface Props {
  booking: BookingState;
}

export default function BookingSuccess({ booking }: Props) {
  const { close } = useTelegram();
  const navigate = useNavigate();

  useEffect(() => {
    try { sessionStorage.removeItem("daina_booking"); } catch {}
  }, []);

  const dateFormatted = booking.date
    ? new Date(booking.date).toLocaleDateString("ru-RU", {
        weekday: "long", day: "numeric", month: "long",
      })
    : "";

  return (
    <motion.div
      className="success"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 100 }}
    >
      <ConfettiAnimation />

      <motion.div
        className="success__icon"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
      >
        ✨
      </motion.div>

      <motion.h1
        className="success__title"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        Вы записаны!
      </motion.h1>

      {booking.serviceName && (
        <motion.div
          className="dashboard-card"
          style={{ textAlign: "left", marginBottom: 16 }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="confirmation__row">
            <span className="confirmation__label">Услуга</span>
            <span className="confirmation__value">{booking.serviceName}</span>
          </div>
          {dateFormatted && (
            <div className="confirmation__row">
              <span className="confirmation__label">Дата</span>
              <span className="confirmation__value">{dateFormatted}</span>
            </div>
          )}
          {booking.time && (
            <div className="confirmation__row">
              <span className="confirmation__label">Время</span>
              <span className="confirmation__value">{booking.time}</span>
            </div>
          )}
          <div className="confirmation__row" style={{ borderBottom: "none" }}>
            <span className="confirmation__label">Стоимость</span>
            <span className="confirmation__value">{booking.servicePrice} руб</span>
          </div>
        </motion.div>
      )}

      <motion.p
        className="success__text"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
      >
        Мастер подтвердит запись в ближайшее время.
        <br />
        Напомню вам за 24 часа и за 2 часа до визита.
      </motion.p>

      <motion.button
        className="btn btn--secondary"
        style={{ marginBottom: 12 }}
        onClick={() => navigate("/contacts")}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.7 }}
        whileTap={{ scale: 0.98 }}
      >
        📞 Контакты мастера
      </motion.button>

      <motion.button
        className="btn btn--primary"
        onClick={close}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        whileTap={{ scale: 0.98 }}
      >
        Закрыть
      </motion.button>
    </motion.div>
  );
}
