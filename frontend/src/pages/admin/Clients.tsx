import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { getClients, ClientItem, createClientFromInstagram } from "../../api/client";

export default function Clients() {
  const [clients, setClients] = useState<ClientItem[]>([]);
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [newIg, setNewIg] = useState("");
  const [newName, setNewName] = useState("");
  const [searching, setSearching] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (search) setSearching(true);
    const timeout = setTimeout(() => {
      getClients(filter, search || undefined)
        .then(setClients)
        .finally(() => setSearching(false));
    }, search ? 300 : 0);
    return () => clearTimeout(timeout);
  }, [filter, search]);

  const addClient = async () => {
    if (!newIg) return;
    try {
      await createClientFromInstagram({
        instagram_handle: newIg.replace("@", ""),
        name: newName || undefined,
      });
      setShowAdd(false);
      setNewIg("");
      setNewName("");
      getClients(filter, search || undefined).then(setClients);
    } catch {
      /* creation failed — form stays open for retry */
    }
  };

  const filters = [
    { key: "all", label: "Все" },
    { key: "vip", label: "VIP" },
    { key: "new", label: "Новые" },
  ];

  return (
    <div>
      <h1 className="page-title">Клиенты</h1>

      <input
        className="search-input"
        placeholder="Поиск по имени или Instagram..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="filter-chips">
        {filters.map((f) => (
          <button
            key={f.key}
            className={`filter-chip ${filter === f.key ? "active" : ""}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
        <button className="filter-chip" onClick={() => setShowAdd(!showAdd)}>
          + Из Instagram
        </button>
      </div>

      {showAdd && (
        <motion.div
          className="dashboard-card"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          style={{ marginBottom: 16 }}
        >
          <div className="dashboard-card__header">Новый клиент из Instagram</div>
          <input
            className="search-input"
            placeholder="@instagram_handle"
            value={newIg}
            onChange={(e) => setNewIg(e.target.value)}
          />
          <input
            className="search-input"
            placeholder="Имя (необязательно)"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <button className="btn btn--primary" onClick={addClient}>
            Добавить и получить ссылку
          </button>
        </motion.div>
      )}

      {searching && <div className="hint">Поиск...</div>}

      {clients.map((c, i) => (
        <motion.div
          key={c.id}
          className="client-item"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.03 }}
          onClick={() => navigate(`/client/${c.id}`)}
        >
          <div className="client-item__avatar">
            {c.first_name.charAt(0).toUpperCase()}
          </div>
          <div className="client-item__info">
            <div className="client-item__name">
              {c.first_name} {c.last_name || ""}
              {c.is_vip && <span className="badge badge--vip" style={{ marginLeft: 6 }}>VIP</span>}
              {c.visit_count === 0 && <span className="badge badge--new" style={{ marginLeft: 6 }}>NEW</span>}
            </div>
            <div className="client-item__meta">
              {c.instagram_handle ? `@${c.instagram_handle}` : c.username ? `@${c.username}` : ""}{" "}
              &bull; {c.visit_count} визитов &bull; {c.total_spent.toLocaleString()} руб
            </div>
          </div>
        </motion.div>
      ))}

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
