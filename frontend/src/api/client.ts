const API_BASE = "/api";

// Auth context — set by the app once telegram user is known
let _authHeaders: Record<string, string> = {};

export function setAuthContext(telegramId: number, initData?: string) {
  _authHeaders = { "X-Telegram-User-Id": String(telegramId) };
  if (initData) {
    _authHeaders["X-Telegram-Init-Data"] = initData;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ..._authHeaders,
        ...options?.headers,
      },
    });
    if (!res.ok) {
      throw new Error(`API error: ${res.status}`);
    }
    return res.json();
  } finally {
    clearTimeout(timeout);
  }
}

// Services
export interface ServiceItem {
  id: number;
  name: string;
  description: string | null;
  duration_minutes: number;
  price: number;
  old_price: number | null;
  photo_url: string | null;
  is_active: boolean;
  sort_order: number;
}

export const getServices = () => request<ServiceItem[]>("/services");
export const getAllServices = () => request<ServiceItem[]>("/services/all");
export const createService = (data: Partial<ServiceItem>) =>
  request<ServiceItem>("/services", { method: "POST", body: JSON.stringify(data) });
export const updateService = (id: number, data: Partial<ServiceItem>) =>
  request<ServiceItem>(`/services/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteService = (id: number) =>
  request(`/services/${id}`, { method: "DELETE" });

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

export const cancelBookingByClient = (bookingId: number, clientId: number) =>
  request(`/bookings/${bookingId}/cancel?client_id=${clientId}`, { method: "PUT" });

// Clients
export interface ClientItem {
  id: number;
  telegram_id: number | null;
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

export const updateClient = (clientId: number, data: Record<string, any>) =>
  request<ClientItem>(`/clients/${clientId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const getClientDetail = (clientId: number) =>
  request<any>(`/clients/${clientId}`);

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
export const getDashboard = (targetDate?: string) =>
  request<any>(targetDate ? `/admin/dashboard?target_date=${targetDate}` : "/admin/dashboard");
export const getStats = (period?: string) =>
  request<any>(`/admin/stats?period=${period || "month"}`);

export const getAllBookings = (status?: string) => {
  const params = status && status !== "all" ? `?status=${status}` : "";
  return request<any[]>(`/admin/all-bookings${params}`);
};

export const deleteBooking = (bookingId: number) =>
  request(`/admin/booking/${bookingId}`, { method: "DELETE" });

export const deleteClientApi = (clientId: number) =>
  request(`/admin/client/${clientId}`, { method: "DELETE" });

// Slots (admin)
export interface SlotItem {
  id: number;
  service_id: number;
  service_name: string;
  date: string;
  time_start: string;
  time_end: string;
  is_booked: boolean;
  booking_id: number | null;
  is_manual_booking: boolean;
  manual_client_name: string | null;
  manual_note: string | null;
  client_name: string | null;
}

export interface SlotCreate {
  service_id: number;
  date: string;
  time_start: string;
  time_end: string;
}

export interface SlotDateSummary {
  date: string;
  total: number;
  available: number;
}

export const getSlotsByDate = (date: string) =>
  request<SlotItem[]>(`/slots?date=${date}`);

export const getSlotDates = (start: string, end: string) =>
  request<SlotDateSummary[]>(`/slots/dates?start=${start}&end=${end}`);

export const createSlot = (data: SlotCreate) =>
  request<SlotItem>("/slots", { method: "POST", body: JSON.stringify(data) });

export const createSlotsBatch = (slots: SlotCreate[]) =>
  request<SlotItem[]>("/slots/batch", {
    method: "POST",
    body: JSON.stringify({ slots }),
  });

export const deleteSlot = (slotId: number) =>
  request(`/slots/${slotId}`, { method: "DELETE" });

export const manualBookSlot = (slotId: number, clientName: string, note?: string) =>
  request<SlotItem>(`/slots/${slotId}/manual-book`, {
    method: "POST",
    body: JSON.stringify({ client_name: clientName, note }),
  });

export const manualUnbookSlot = (slotId: number) =>
  request<SlotItem>(`/slots/${slotId}/manual-unbook`, { method: "POST" });

// Config
export interface PublicConfig {
  app_name: string;
  bot_username: string;
  studio_address: string;
  master_username: string;
  currency: string;
}

export const getPublicConfig = () => request<PublicConfig>("/config/public");

export const checkAdmin = (telegramId: number, initData?: string) => {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Telegram-User-Id": String(telegramId),
  };
  if (initData) {
    headers["X-Telegram-Init-Data"] = initData;
  }
  return fetch(`${API_BASE}/config/check-admin`, { headers }).then((r) =>
    r.ok ? r.json() : { is_admin: false }
  ) as Promise<{ is_admin: boolean; telegram_id?: number }>;
};

export const getAdminConfig = () =>
  request<Record<string, string>>("/config");

export const updateAdminConfig = (values: Record<string, string>) =>
  request("/config", {
    method: "PUT",
    body: JSON.stringify({ values }),
  });
