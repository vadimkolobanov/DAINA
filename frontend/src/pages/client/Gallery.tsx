import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { useTelegram } from "../../hooks/useTelegram";
import { useEffect } from "react";

const INSTAGRAM_URL = "https://www.instagram.com/glodia_nails_brest?utm_source=telegram&utm_medium=miniapp&utm_campaign=gallery";

export default function Gallery() {
  const navigate = useNavigate();
  const { tg } = useTelegram();

  useEffect(() => {
    tg?.BackButton?.show();
    const back = () => navigate("/");
    tg?.BackButton?.onClick(back);
    return () => {
      tg?.BackButton?.offClick(back);
      tg?.BackButton?.hide();
    };
  }, []);

  return (
    <div>
      <motion.h1
        className="page-title"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        Наши работы
      </motion.h1>

      <motion.div
        className="dashboard-card"
        style={{ textAlign: "center", padding: 32 }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div style={{ fontSize: 48, marginBottom: 12 }}>💅</div>
        <div style={{ fontSize: 15, color: "var(--tg-theme-hint-color)", lineHeight: 1.5, marginBottom: 16 }}>
          Смотрите наши работы в Instagram!
          <br />
          Там вы найдёте примеры дизайнов, отзывы клиентов и вдохновение для вашего маникюра.
        </div>
        <button
          className="btn btn--primary"
          onClick={() => tg?.openLink(INSTAGRAM_URL)}
        >
          📷 Открыть Instagram
        </button>
      </motion.div>

      <button
        className="btn btn--secondary"
        style={{ marginTop: 16 }}
        onClick={() => navigate("/")}
      >
        Назад к услугам
      </button>
    </div>
  );
}
