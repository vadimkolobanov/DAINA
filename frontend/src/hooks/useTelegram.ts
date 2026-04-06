import { useCallback, useEffect, useMemo, useState } from "react";
import { checkAdmin } from "../api/client";

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
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminChecked, setAdminChecked] = useState(false);

  useEffect(() => {
    tg?.ready();
    tg?.expand();
  }, [tg]);

  const user = tg?.initDataUnsafe?.user;
  const startParam = tg?.initDataUnsafe?.start_param;
  const initData = tg?.initData;

  // Check if admin mode was requested via start_param or URL query
  const adminRequested = startParam === "admin"
    || new URLSearchParams(window.location.search).get("startapp") === "admin";

  // Validate admin access via server
  useEffect(() => {
    if (!user) {
      setAdminChecked(true);
      return;
    }
    if (!adminRequested) {
      setAdminChecked(true);
      return;
    }
    checkAdmin(user.id, initData)
      .then((result) => {
        setIsAdmin(result.is_admin);
        setAdminChecked(true);
      })
      .catch(() => {
        setIsAdmin(false);
        setAdminChecked(true);
      });
  }, [user, adminRequested, initData]);

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
    initData,
    isAdmin,
    adminChecked,
    haptic,
    hapticSuccess,
    hapticError,
    close,
  };
}
