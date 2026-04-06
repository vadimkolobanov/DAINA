import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useTelegram } from "../../hooks/useTelegram";
import { getPublicConfig } from "../../api/client";

export default function MasterContacts() {
  const navigate = useNavigate();
  const { tg } = useTelegram();
  const [config, setConfig] = useState<Record<string, string>>({});

  useEffect(() => {
    tg?.BackButton?.show();
    const back = () => navigate("/");
    tg?.BackButton?.onClick(back);
    getPublicConfig().then((c) => setConfig(c as any)).catch(() => {});
    return () => {
      tg?.BackButton?.offClick(back);
      tg?.BackButton?.hide();
    };
  }, []);

  const name = config.master_name || "Мастер";
  const username = (config.master_username || "").replace("@", "");
  const phone = config.master_phone || "";
  const instagram = (config.master_instagram || "").replace("@", "");
  const address = config.studio_address || "";
  const mapUrl = config.studio_map_url || "";

  return (
    <div>
      <motion.h1
        className="page-title"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        Контакты
      </motion.h1>

      <motion.div
        className="dashboard-card"
        style={{ textAlign: "center", paddingTop: 24, paddingBottom: 24 }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div style={{ fontSize: 48, marginBottom: 8 }}>💅</div>
        <h2 style={{ fontSize: 22, marginBottom: 16 }}>{name}</h2>

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {phone && (
            <button
              className="btn btn--secondary"
              onClick={() => {
                navigator.clipboard.writeText(phone);
                tg?.showAlert?.(`Скопировано: ${phone}`);
              }}
            >
              📞 {phone}
            </button>
          )}

          {username && (
            <button
              className="btn btn--secondary"
              onClick={() => tg?.openTelegramLink(`https://t.me/${username}`)}
            >
              ✈️ Написать в Telegram
            </button>
          )}

          {instagram && (
            <button
              className="btn btn--secondary"
              onClick={() => tg?.openLink(`https://www.instagram.com/${instagram}?utm_source=telegram&utm_medium=miniapp&utm_campaign=contacts`)}
            >
              📷 Instagram: @{instagram}
            </button>
          )}

          {address && (
            <button
              className="btn btn--secondary"
              onClick={() => mapUrl ? tg?.openLink(mapUrl) : undefined}
              style={!mapUrl ? { cursor: "default" } : {}}
            >
              📍 {address}
            </button>
          )}
        </div>
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
