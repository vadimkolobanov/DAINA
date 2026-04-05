import { useCallback, useEffect, useMemo } from "react";

declare global {
  interface Window {
    Telegram: {
      WebApp: {
        ready: () => void;
        close: () => void;
        expand: () => void;
        MainButton: {
          text: string;
          color: string;
          textColor: string;
          isVisible: boolean;
          isActive: boolean;
          show: () => void;
          hide: () => void;
          onClick: (cb: () => void) => void;
          offClick: (cb: () => void) => void;
          setText: (text: string) => void;
          enable: () => void;
          disable: () => void;
          showProgress: (leaveActive?: boolean) => void;
          hideProgress: () => void;
        };
        BackButton: {
          isVisible: boolean;
          show: () => void;
          hide: () => void;
          onClick: (cb: () => void) => void;
          offClick: (cb: () => void) => void;
        };
        HapticFeedback: {
          impactOccurred: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
          notificationOccurred: (type: "error" | "success" | "warning") => void;
          selectionChanged: () => void;
        };
        initDataUnsafe: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
          };
          start_param?: string;
        };
        initData: string;
        colorScheme: "light" | "dark";
        themeParams: Record<string, string>;
      };
    };
  }
}

export function useTelegram() {
  const tg = useMemo(() => window.Telegram?.WebApp, []);

  useEffect(() => {
    tg?.ready();
    tg?.expand();
  }, [tg]);

  const user = tg?.initDataUnsafe?.user;
  const startParam = tg?.initDataUnsafe?.start_param;
  const isAdmin = startParam === "admin" || new URLSearchParams(window.location.search).get("mode") === "admin";

  const haptic = useCallback(
    (type: "light" | "medium" | "heavy" = "light") => {
      tg?.HapticFeedback?.impactOccurred(type);
    },
    [tg]
  );

  const hapticSuccess = useCallback(() => {
    tg?.HapticFeedback?.notificationOccurred("success");
  }, [tg]);

  const hapticError = useCallback(() => {
    tg?.HapticFeedback?.notificationOccurred("error");
  }, [tg]);

  const close = useCallback(() => {
    tg?.close();
  }, [tg]);

  return {
    tg,
    user,
    startParam,
    isAdmin,
    haptic,
    hapticSuccess,
    hapticError,
    close,
  };
}
