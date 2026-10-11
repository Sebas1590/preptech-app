import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { useAiStatus } from "@/lib/api";

export const Route = createFileRoute("/ia")({
  head: () => ({
    meta: [
      { title: "Configuración de IA | PrepTech" },
      { name: "description", content: "Conecta tu API Key para activar el Coach y las pistas del módulo IoT." },
    ],
  }),
  component: ConfigIA,
});

function ConfigIA() {
  const { status, offline, connect, test, disconnect } = useAiStatus();
  const [clave, setClave] = useState("");
  const [modelo, setModelo] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const accion = async (fn: () => Promise<void>) => {
    setCargando(true);
    setError(null);
    try {
      await fn();
      setClave("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error inesperado");
    } finally {
      setCargando(false);
    }
  };

  const conectado = !!status?.connected;
  const campo =
    "mt-2 w-full rounded-sm border border-input bg-surface-2 p-3 font-mono text-sm outline-none focus:border-primary";

  return (
    <AppShell titulo="Configuración de IA" subtitulo="Conexión con el modelo que potencia el Coach y el módulo IoT">
      <div className="grid max-w-4xl gap-6 lg:grid-cols-5">
        <section className="panel space-y-5 p-5 lg:col-span-3">
          <label className="block">
            <span className="label-xs">API Key de OpenAI</span>
            <input
              type="password"
              autoComplete="off"
              spellCheck={false}
              placeholder="sk-…"
              value={clave}
              onChange={(e) => setClave(e.target.value)}
              className={campo}
            />
            <span className="mt-2 block text-xs text-muted-foreground">
              Se envía una sola vez al backend y vive solo en su memoria. No se guarda en el navegador ni en disco.
            </span>
          </label>
          <label className="block">
            <span className="label-xs">Modelo (opcional)</span>
            <input
              placeholder={status?.model ?? "gpt-4.1-mini"}
              value={modelo}
              onChange={(e) => setModelo(e.target.value)}
              className={campo}
            />
          </label>

          {error ? (
            <p role="alert" className="rounded-sm border border-signal px-3 py-2 text-sm text-signal">
              {error}
            </p>
          ) : null}

          <div className="flex flex-wrap gap-2">
            <button
              disabled={cargando || clave.trim().length < 8}
              onClick={() => accion(() => connect(clave.trim(), modelo.trim()))}
              className="rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-40"
            >
              {cargando ? "Conectando…" : "Conectar"}
            </button>
            <button
              disabled={cargando || !status?.configured}
              onClick={() => accion(test)}
              className="rounded-sm border border-border bg-surface-2 px-4 py-2 text-sm disabled:opacity-40"
            >
              Probar conexión
            </button>
            <button
              disabled={cargando || status?.source !== "interfaz"}
              onClick={() => accion(disconnect)}
              className="rounded-sm border border-border bg-surface-2 px-4 py-2 text-sm text-muted-foreground disabled:opacity-40"
            >
              Desconectar
            </button>
          </div>
        </section>

        <aside className="panel space-y-4 p-5 lg:col-span-2" aria-live="polite">
          <p className="label-xs">Estado</p>
          <div className="flex items-center gap-3">
            <span
              className={`size-3 rounded-full ${offline ? "bg-signal" : conectado ? "bg-primary" : "bg-muted-foreground"}`}
            />
            <span className="font-display text-xl font-semibold">
              {offline ? "Backend sin conexión" : conectado ? "Conectado" : status?.configured ? "Sin verificar" : "Desconectado"}
            </span>
          </div>
          <dl className="space-y-2 font-mono text-xs text-muted-foreground">
            <div className="flex justify-between"><dt>Modelo</dt><dd>{status?.model ?? "—"}</dd></div>
            <div className="flex justify-between"><dt>Clave</dt><dd>{status?.key_hint ?? "—"}</dd></div>
            <div className="flex justify-between"><dt>Origen</dt><dd>{status?.source ?? "—"}</dd></div>
            <div className="flex justify-between">
              <dt>Verificada</dt>
              <dd>{status?.connected_at ? new Date(status.connected_at).toLocaleTimeString() : "—"}</dd>
            </div>
          </dl>
          {offline ? (
            <p className="text-xs text-muted-foreground">
              Inicia la API: <code>uvicorn server:app --port 8000</code> dentro de <code>preptech-ai</code>.
            </p>
          ) : null}
          <p className="border-t border-border pt-3 text-xs text-muted-foreground">
            La IA es orientativa: no predice contrataciones ni reemplaza la práctica real.
          </p>
        </aside>
      </div>
    </AppShell>
  );
}
