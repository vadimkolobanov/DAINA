import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import TimeSlots from "../../components/TimeSlots";
import StepIndicator from "../../components/StepIndicator";
import { useTelegram } from "../../hooks/useTelegram";
import { BookingState } from "../../App";
import { useEffect } from "react";

interface Props {
  booking: BookingState;
  setBooking: (b: BookingState) => void;
}

export default function TimeSelect({ booking, setBooking }: Props) {
  const navigate = useNavigate();
  const { haptic, tg } = useTelegram();

  useEffect(() => {
    if (!booking.date) {
      navigate("/");
    }
    tg?.BackButton?.show();
    const back = () => navigate("/date");
    tg?.BackButton?.onClick(back);
    return () => {
      tg?.BackButton?.offClick(back);
      tg?.BackButton?.hide();
    };
  }, []);

  const onSelectTime = (time: string) => {
    haptic("medium");
    setBooking({ ...booking, time });
    navigate("/confirm");
  };

  const dateFormatted = booking.date
    ? new Date(booking.date).toLocaleDateString("ru-RU", {
        weekday: "long",
        day: "numeric",
        month: "long",
      })
    : "";

  return (
    <motion.div initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }}>
      <StepIndicator current={2} total={4} />
      <h1 className="page-title">Выберите время</h1>
      <p className="page-subtitle">
        {booking.serviceName} &bull; {dateFormatted}
      </p>

      <TimeSlots
        date={booking.date}
        serviceId={booking.serviceId!}
        selectedTime={booking.time}
        onSelect={onSelectTime}
      />
    </motion.div>
  );
}
