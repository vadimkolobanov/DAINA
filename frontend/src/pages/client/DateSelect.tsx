import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import Calendar from "../../components/Calendar";
import StepIndicator from "../../components/StepIndicator";
import { useTelegram } from "../../hooks/useTelegram";
import { BookingState } from "../../App";
import { useEffect } from "react";

interface Props {
  booking: BookingState;
  setBooking: (b: BookingState) => void;
}

export default function DateSelect({ booking, setBooking }: Props) {
  const navigate = useNavigate();
  const { haptic, tg } = useTelegram();

  useEffect(() => {
    if (!booking.serviceId) {
      navigate("/");
    }
    tg?.BackButton?.show();
    const back = () => navigate("/");
    tg?.BackButton?.onClick(back);
    return () => {
      tg?.BackButton?.offClick(back);
      tg?.BackButton?.hide();
    };
  }, []);

  const onSelectDate = (date: string) => {
    haptic("light");
    setBooking({ ...booking, date });
    navigate("/time");
  };

  return (
    <motion.div initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }}>
      <StepIndicator current={1} total={4} />
      <h1 className="page-title">Выберите дату</h1>
      <p className="page-subtitle">{booking.serviceName}</p>

      <Calendar
        serviceId={booking.serviceId!}
        serviceDuration={booking.serviceDuration}
        selectedDate={booking.date}
        onSelect={onSelectDate}
      />
    </motion.div>
  );
}
