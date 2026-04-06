import { Routes, Route, Navigate } from "react-router-dom";
import { useTelegram } from "./hooks/useTelegram";
import { setAuthContext, getClientByTelegram, ClientItem } from "./api/client";
import ServiceSelect from "./pages/client/ServiceSelect";
import DateSelect from "./pages/client/DateSelect";
import TimeSelect from "./pages/client/TimeSelect";
import Confirmation from "./pages/client/Confirmation";
import BookingSuccess from "./pages/client/BookingSuccess";
import MyBookings from "./pages/client/MyBookings";
import ProfileSetup from "./pages/client/ProfileSetup";
import Dashboard from "./pages/admin/Dashboard";
import Clients from "./pages/admin/Clients";
import ClientCard from "./pages/admin/ClientCard";
import AllBookings from "./pages/admin/AllBookings";
import Schedule from "./pages/admin/Schedule";
import Statistics from "./pages/admin/Statistics";
import Settings from "./pages/admin/Settings";
import { useEffect, useState } from "react";

export interface BookingState {
  serviceId: number | null;
  serviceName: string;
  servicePrice: number;
  serviceDuration: number;
  date: string;
  time: string;
}

const STORAGE_KEY = "daina_booking";

function usePersistedBooking() {
  const [booking, setBookingRaw] = useState<BookingState>(() => {
    try {
      const saved = sessionStorage.getItem(STORAGE_KEY);
      if (saved) return JSON.parse(saved);
    } catch {}
    return { serviceId: null, serviceName: "", servicePrice: 0, serviceDuration: 0, date: "", time: "" };
  });

  const setBooking = (b: BookingState) => {
    setBookingRaw(b);
    try { sessionStorage.setItem(STORAGE_KEY, JSON.stringify(b)); } catch {}
  };

  const clearBooking = () => {
    setBookingRaw({ serviceId: null, serviceName: "", servicePrice: 0, serviceDuration: 0, date: "", time: "" });
    try { sessionStorage.removeItem(STORAGE_KEY); } catch {}
  };

  return { booking, setBooking, clearBooking };
}

export default function App() {
  const { isAdmin, adminChecked, user, initData } = useTelegram();

  // Set auth context for API calls
  useEffect(() => {
    if (user) {
      setAuthContext(user.id, initData);
    }
  }, [user, initData]);
  const { booking, setBooking, clearBooking } = usePersistedBooking();

  // Client profile check — load client and check if phone exists
  const [clientProfile, setClientProfile] = useState<ClientItem | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [needsProfile, setNeedsProfile] = useState(false);

  useEffect(() => {
    if (!user || isAdmin) {
      setProfileLoading(false);
      return;
    }
    getClientByTelegram(user.id)
      .then((client) => {
        setClientProfile(client);
        setNeedsProfile(!client.phone);
        setProfileLoading(false);
      })
      .catch(() => {
        // Client not found in DB yet (hasn't run /start)
        setNeedsProfile(true);
        setProfileLoading(false);
      });
  }, [user, isAdmin]);

  if (!adminChecked || (!isAdmin && profileLoading)) {
    return <div className="app"><div className="hint">Загрузка...</div></div>;
  }

  if (isAdmin) {
    return (
      <div className="app">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/clients" element={<Clients />} />
          <Route path="/client/:clientId" element={<ClientCard />} />
          <Route path="/all-bookings" element={<AllBookings />} />
          <Route path="/schedule" element={<Schedule />} />
          <Route path="/stats" element={<Statistics />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    );
  }

  if (needsProfile) {
    if (!clientProfile) {
      return (
        <div className="app">
          <div style={{ textAlign: "center", padding: "40px 16px" }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>💅</div>
            <h1 className="page-title">Добро пожаловать!</h1>
            <p className="page-subtitle">
              Чтобы записаться, сначала нажмите <b>Start</b> в боте, затем откройте приложение снова.
            </p>
          </div>
        </div>
      );
    }
    return (
      <div className="app">
        <ProfileSetup
          clientId={clientProfile.id}
          existingPhone={clientProfile.phone}
          existingInstagram={clientProfile.instagram_handle}
          onComplete={() => setNeedsProfile(false)}
        />
      </div>
    );
  }

  return (
    <div className="app">
      <Routes>
        <Route
          path="/"
          element={<ServiceSelect booking={booking} setBooking={setBooking} />}
        />
        <Route
          path="/date"
          element={<DateSelect booking={booking} setBooking={setBooking} />}
        />
        <Route
          path="/time"
          element={<TimeSelect booking={booking} setBooking={setBooking} />}
        />
        <Route
          path="/confirm"
          element={<Confirmation booking={booking} />}
        />
        <Route path="/success" element={<BookingSuccess />} />
        <Route path="/my-bookings" element={<MyBookings />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </div>
  );
}
