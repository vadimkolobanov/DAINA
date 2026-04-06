import { Routes, Route, Navigate } from "react-router-dom";
import { useTelegram } from "./hooks/useTelegram";
import { setAuthContext } from "./api/client";
import ServiceSelect from "./pages/client/ServiceSelect";
import DateSelect from "./pages/client/DateSelect";
import TimeSelect from "./pages/client/TimeSelect";
import Confirmation from "./pages/client/Confirmation";
import BookingSuccess from "./pages/client/BookingSuccess";
import MyBookings from "./pages/client/MyBookings";
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

export default function App() {
  const { isAdmin, adminChecked, user, initData } = useTelegram();

  // Set auth context for API calls
  useEffect(() => {
    if (user) {
      setAuthContext(user.id, initData);
    }
  }, [user, initData]);
  const [booking, setBooking] = useState<BookingState>({
    serviceId: null,
    serviceName: "",
    servicePrice: 0,
    serviceDuration: 0,
    date: "",
    time: "",
  });

  if (!adminChecked) {
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
