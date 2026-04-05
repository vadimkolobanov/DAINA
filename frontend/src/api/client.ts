const API_BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

// Services
export interface ServiceItem {
  id: number;
  name: string;
  description: string | null;
  duration_minutes: number;
  price: number;
  photo_url: string | null;
  is_active: boolean;
}

export const getServices = () => request<ServiceItem[]>("/services");

// Bookings
export interface TimeSlot {
  time: string;
}

export interface DateAvailability {
  date: string;
  available: boolean;
  slots_count: number;
}

export const getAvailableSlots = (date: string, serviceId: number) =>
  request<TimeSlot[]>("/bookings/available-slots", {
    method: "POST",
    body: JSON.stringify({ date, service_id: serviceId }),
  });

export const getAvailableDates = (serviceId: number, start: string, end: string) =>
  request<DateAvailability[]>(
    `/bookings/available-dates?service_id=${serviceId}&start=${start}&end=${end}`
  );

export interface BookingCreate {
  client_id: number;
  service_id: number;
  date: string;
  time: string;
}

export const createBooking = (data: BookingCreate) =>
  request("/bookings", { method: "POST", body: JSON.stringify(data) });

export const getClientBookings = (clientId: number) =>
  request(`/bookings/client/${clientId}`);

export const getBookingsByDate = (date: string) =>
  request(`/bookings/by-date/${date}`);

export const updateBookingStatus = (bookingId: number, status: string) =>
  request(`/bookings/${bookingId}/status?status=${status}`, { method: "PUT" });

// Clients
export interface ClientItem {
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
}

export const getClientByTelegram = (telegramId: number) =>
  request<ClientItem>(`/clients/telegram/${telegramId}`);

export const getClients = (filter?: string, q?: string) => {
  const params = new URLSearchParams();
  if (filter) params.set("filter", filter);
  if (q) params.set("q", q);
  return request<ClientItem[]>(`/clients?${params}`);
};

export const createClientFromInstagram = (data: {
  instagram_handle: string;
  name?: string;
  phone?: string;
  notes?: string;
}) => request<ClientItem>("/clients/from-instagram", { method: "POST", body: JSON.stringify(data) });

// Schedule
export interface ScheduleDay {
  day_of_week: number;
  is_working: boolean;
  time_start: string;
  time_end: string;
}

export const getSchedule = () => request<ScheduleDay[]>("/schedule");

export const updateScheduleDay = (data: ScheduleDay) =>
  request("/schedule/day", { method: "PUT", body: JSON.stringify(data) });

// Admin
export const getDashboard = () => request<any>("/admin/dashboard");
export const getStats = (period?: string) =>
  request<any>(`/admin/stats?period=${period || "month"}`);
