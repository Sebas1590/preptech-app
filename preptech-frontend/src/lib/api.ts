import { useCallback, useEffect, useState } from "react";

const BASE = (import.meta.env["VITE_API_URL"] as string | undefined) ?? "/api";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function api<T>(path: string, init: { method?: string; json?: unknown } = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      method: init.method ?? "GET",
      headers: { "Content-Type": "application/json" },
      ...(init.json !== undefined ? { body: JSON.stringify(init.json) } : {}),
    });
  } catch {
    throw new ApiError("No se pudo conectar con el backend. ¿Está corriendo en el puerto 8000?", 0);
  }
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const d = data?.detail;
    const msg = typeof d === "string" ? d : Array.isArray(d) ? d.map((x) => x.msg).join("; ") : `Error ${res.status}`;
    throw new ApiError(msg, res.status);
  }
  return data as T;
}

export type AiStatus = {
  configured: boolean;
  connected: boolean;
  source: "interfaz" | "entorno" | null;
  key_hint: string | null;
  model: string;
  connected_at: string | null;
};

type Listener = (s: AiStatus | null, offline: boolean) => void;
let current: AiStatus | null = null;
let offline = false;
const listeners = new Set<Listener>();

function publish(s: AiStatus | null, off: boolean) {
  current = s;
  offline = off;
  listeners.forEach((fn) => fn(s, off));
}

export function useAiStatus() {
  const [status, setStatus] = useState<AiStatus | null>(current);
  const [off, setOff] = useState(offline);

  useEffect(() => {
    const fn: Listener = (s, o) => {
      setStatus(s);
      setOff(o);
    };
    listeners.add(fn);
    if (!current) void refresh();
    return () => {
      listeners.delete(fn);
    };
  }, []);

  const refresh = useCallback(async () => {
    try {
      publish(await api<AiStatus>("/ai/status"), false);
    } catch {
      publish(null, true);
    }
  }, []);

  const connect = useCallback(async (api_key: string, model?: string) => {
    publish(await api<AiStatus>("/ai/connect", { method: "POST", json: { api_key, model: model || null } }), false);
  }, []);

  const test = useCallback(async () => {
    publish(await api<AiStatus>("/ai/test", { method: "POST" }), false);
  }, []);

  const disconnect = useCallback(async () => {
    publish(await api<AiStatus>("/ai/connect", { method: "DELETE" }), false);
  }, []);

  return { status, offline: off, refresh, connect, test, disconnect };
}
