import { useEffect } from "react";
import confetti from "canvas-confetti";

export default function ConfettiAnimation() {
  useEffect(() => {
    const end = Date.now() + 2000;
    const colors = ["#d4a0c0", "#f0dce8", "#b07a9e", "#ffd700", "#ff69b4"];

    const frame = () => {
      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0 },
        colors,
      });
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1 },
        colors,
      });
      if (Date.now() < end) {
        requestAnimationFrame(frame);
      }
    };
    frame();
  }, []);

  return null;
}
