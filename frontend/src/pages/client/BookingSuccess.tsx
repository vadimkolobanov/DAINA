import { motion } from "framer-motion";
import ConfettiAnimation from "../../components/ConfettiAnimation";
import { useTelegram } from "../../hooks/useTelegram";

export default function BookingSuccess() {
  const { close } = useTelegram();

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

      <motion.p
        className="success__text"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.6 }}
      >
        Мастер подтвердит вашу запись в ближайшее время.
        <br />
        Я напомню вам за 24 часа и за 2 часа до визита.
      </motion.p>

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
