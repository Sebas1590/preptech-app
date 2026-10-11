import { createFileRoute, Link } from "@tanstack/react-router";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api, useAiStatus } from "@/lib/api";

export const Route = createFileRoute("/iot")({
  head: () => ({
    meta: [
      { title: "Módulo IoT | PrepTech" },
      { name: "description", content: "Programa un ESP32 simulado: LED, botón y sensores, sin hardware." },
    ],
  }),
  component: Iot,
});

type Device = { type: "led" | "button" | "sensor"; pin: number; label: string; color?: string };
type Control =
  | { type: "button"; pin: number; label: string }
  | { type: "slider"; pin: number; label: string; min: number; max: number; value: number };
type Lesson = {
  id: string;
  titulo: string;
  nivel: string;
  board: string;
  objetivo: string;
  teoria: string[];
  devices: Device[];
  controls: Control[];
  starter: string;
};
type PinEvent = { t: number; pin: number; kind: "mode" | "digital" | "pwm"; value: number | string };
type Sim = {
  ok: boolean;
  error: string | null;
  error_line: number | null;
  events: PinEvent[];
  serial: { t: number; text: string }[];
  warnings: string[];
  duration_ms: number;
  checks?: { label: string; ok: boolean }[];
  passed?: boolean;
};
type Boton = "suelto" | "presionado" | "auto";

function pinLevel(events: PinEvent[], pin: number, t: number) {
  let v = 0;
  let pwm = false;
  for (const e of events) {
    if (e.pin === pin && e.t <= t && (e.kind === "digital" || e.kind === "pwm")) {
      v = e.value as number;
      pwm = e.kind === "pwm";
    }
  }
  return pwm ? v / 255 : v;
}

function Iot() {
  const { status } = useAiStatus();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [idx, setIdx] = useState(0);
  const [codigos, setCodigos] = useState<Record<string, string>>({});
  const [boton, setBoton] = useState<Boton>("auto");
  const [sliders, setSliders] = useState<Record<number, number>>({});
  const [sim, setSim] = useState<Sim | null>(null);
  const [t, setT] = useState(0);
  const [corriendo, setCorriendo] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pista, setPista] = useState<string | null>(null);
  const [pidiendo, setPidiendo] = useState(false);
  const raf = useRef<number | null>(null);

  useEffect(() => {
    api<Lesson[]>("/iot/lessons")
      .then(setLessons)
      .catch((e) => setError(e instanceof Error ? e.message : "Error"));
  }, []);

  const lesson = lessons[idx];
  const codigo = lesson ? (codigos[lesson.id] ?? lesson.starter) : "";

  const detener = useCallback(() => {
    if (raf.current) cancelAnimationFrame(raf.current);
    raf.current = null;
    setCorriendo(false);
  }, []);
  useEffect(() => detener, [detener]);

  const reproducir = (duracion: number) => {
    detener();
    const inicio = performance.now();
    setCorriendo(true);
    const paso = (now: number) => {
      const el = Math.min(duracion, now - inicio);
      setT(el);
      if (el < duracion) raf.current = requestAnimationFrame(paso);
      else detener();
    };
    raf.current = requestAnimationFrame(paso);
  };

  const inputs = useMemo(() => {
    const out: Record<string, number | number[][]> = {};
    lesson?.controls.forEach((c) => {
      if (c.type === "button") out[c.pin] = boton === "presionado" ? 1 : boton === "auto" ? [[1000, 1], [2500, 0]] : 0;
      else out[c.pin] = sliders[c.pin] ?? c.value;
    });
    return out;
  }, [lesson, boton, sliders]);

  const ejecutar = async () => {
    if (!lesson) return;
    setCargando(true);
    setError(null);
    setPista(null);
    try {
      const r = await api<Sim>("/iot/simulate", {
        method: "POST",
        json: { code: codigo, board: lesson.board, lesson_id: lesson.id, inputs, duration_ms: 5000 },
      });
      setSim(r);
      setT(0);
      if (r.ok) reproducir(r.duration_ms || 5000);
      else detener();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error inesperado");
    } finally {
      setCargando(false);
    }
  };

  const pedirPista = async () => {
    if (!lesson) return;
    setPidiendo(true);
    setPista(null);
    try {
      const resumen = sim
        ? sim.ok
          ? `Ejecutó sin errores. Checks: ${(sim.checks ?? []).map((c) => `${c.ok ? "OK" : "FALLA"}: ${c.label}`).join("; ")}`
          : `Error en línea ${sim.error_line}: ${sim.error}`
        : "";
      const r = await api<{ text: string }>("/iot/hint", {
        method: "POST",
        json: { lesson_id: lesson.id, code: codigo, result_summary: resumen },
      });
      setPista(r.text);
    } catch (e) {
      setPista(e instanceof Error ? e.message : "Error inesperado");
    } finally {
      setPidiendo(false);
    }
  };

  const cambiarLeccion = (i: number) => {
    detener();
    setIdx(i);
    setSim(null);
    setT(0);
    setPista(null);
    setError(null);
  };

  const serialVisible = sim?.serial.filter((s) => s.t <= t) ?? [];
  const pulsado =
    lesson?.controls.some((c) => c.type === "button") &&
    (boton === "presionado" || (boton === "auto" && t >= 1000 && t < 2500 && !!sim));

  return (
    <AppShell
      titulo="Módulo IoT"
      subtitulo="ESP32 simulado por software · sin hardware, costo 0"
      acciones={
        <span className="rounded-sm border border-border px-2 py-1 font-mono text-[11px] text-muted-foreground">
          IA: {status?.connected ? "conectada" : "desconectada"}
        </span>
      }
    >
      {error ? (
        <p role="alert" className="mb-4 rounded-sm border border-signal px-3 py-2 text-sm text-signal">
          {error}
        </p>
      ) : null}
      {!lesson ? (
        <p className="text-sm text-muted-foreground">Cargando lecciones…</p>
      ) : (
        <div className="grid gap-6 xl:grid-cols-5">
          <div className="space-y-4 xl:col-span-2">
            <nav className="flex flex-wrap gap-2" aria-label="Lecciones">
              {lessons.map((l, i) => (
                <button
                  key={l.id}
                  onClick={() => cambiarLeccion(i)}
                  className={`rounded-sm border px-3 py-1.5 text-sm ${
                    i === idx ? "border-primary bg-primary text-primary-foreground" : "border-border bg-surface-2"
                  }`}
                >
                  {l.titulo}
                </button>
              ))}
            </nav>
            <section className="panel space-y-3 p-5">
              <p className="label-xs">
                {lesson.nivel} · {lesson.board.toUpperCase()}
              </p>
              <p className="text-sm font-medium">{lesson.objetivo}</p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-foreground/80">
                {lesson.teoria.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ul>
            </section>

            <section className="panel space-y-3 p-5">
              <p className="label-xs">Mundo físico simulado</p>
              {lesson.controls.length === 0 ? (
                <p className="text-xs text-muted-foreground">Esta lección no tiene entradas externas.</p>
              ) : null}
              {lesson.controls.map((c) =>
                c.type === "button" ? (
                  <label key={c.pin} className="block text-sm">
                    {c.label}
                    <select
                      value={boton}
                      onChange={(e) => setBoton(e.target.value as Boton)}
                      className="mt-1 w-full rounded-sm border border-input bg-surface-2 p-2 text-sm"
                    >
                      <option value="suelto">Suelto</option>
                      <option value="presionado">Presionado todo el tiempo</option>
                      <option value="auto">Pulsación automática (1.0 s – 2.5 s)</option>
                    </select>
                  </label>
                ) : (
                  <label key={c.pin} className="block text-sm">
                    {c.label}: <span className="font-mono">{sliders[c.pin] ?? c.value}%</span>
                    <input
                      type="range"
                      min={c.min}
                      max={c.max}
                      value={sliders[c.pin] ?? c.value}
                      onChange={(e) => setSliders((s) => ({ ...s, [c.pin]: Number(e.target.value) }))}
                      className="mt-1 w-full accent-[var(--primary)]"
                    />
                  </label>
                ),
              )}
            </section>
          </div>

          <div className="space-y-4 xl:col-span-3">
            <section className="panel overflow-hidden">
              <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
                <span className="font-mono text-[11px] text-muted-foreground">sketch.ino</span>
                <span className="font-mono text-[11px] text-muted-foreground">{codigo.split("\n").length} líneas</span>
              </div>
              <textarea
                value={codigo}
                onChange={(e) => setCodigos((c) => ({ ...c, [lesson.id]: e.target.value }))}
                spellCheck={false}
                aria-label="Código del sketch"
                className="min-h-[300px] w-full resize-y bg-surface-2 p-4 font-mono text-[13px] leading-relaxed outline-none"
              />
              <div className="flex flex-wrap gap-2 border-t border-border p-4">
                <button
                  onClick={ejecutar}
                  disabled={cargando}
                  className="rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50"
                >
                  {cargando ? "Compilando…" : "▶ Compilar y simular"}
                </button>
                <button
                  onClick={() => {
                    setCodigos((c) => ({ ...c, [lesson.id]: lesson.starter }));
                    setSim(null);
                    detener();
                  }}
                  className="rounded-sm border border-border bg-surface-2 px-4 py-2 text-sm"
                >
                  Restablecer
                </button>
                <button
                  onClick={pedirPista}
                  disabled={pidiendo || !status?.connected}
                  title={status?.connected ? "" : "Conecta la IA en Configuración de IA"}
                  className="ml-auto rounded-sm border border-border bg-surface-2 px-4 py-2 text-sm disabled:opacity-40"
                >
                  {pidiendo ? "Pensando…" : "💡 Pista con IA"}
                </button>
              </div>
            </section>

            {sim && !sim.ok ? (
              <p role="alert" className="rounded-sm border border-signal px-3 py-2 font-mono text-sm text-signal">
                Error de compilación{sim.error_line ? ` (línea ${sim.error_line})` : ""}: {sim.error}
              </p>
            ) : null}
            {!status?.connected ? (
              <p className="text-xs text-muted-foreground">
                Las pistas con IA requieren conexión.{" "}
                <Link to="/ia" className="text-primary underline">
                  Configurar IA
                </Link>
              </p>
            ) : null}
            {pista ? <p className="panel whitespace-pre-wrap p-4 text-sm">💡 {pista}</p> : null}

            <div className="grid gap-4 lg:grid-cols-2">
              <section className="panel p-4" aria-label="Placa simulada">
                <p className="label-xs mb-3">Placa · t = {(t / 1000).toFixed(1)} s {corriendo ? "▶" : ""}</p>
                <svg viewBox="0 0 300 190" className="w-full" role="img" aria-label="ESP32 con dispositivos simulados">
                  <rect x="20" y="20" width="150" height="150" rx="6" fill="var(--surface-2)" stroke="var(--border)" />
                  <text x="95" y="50" textAnchor="middle" fontSize="11" fill="var(--muted-foreground)">
                    {lesson.board === "esp32" ? "ESP32" : "ARDUINO"}
                  </text>
                  {lesson.devices.map((d, i) => {
                    const y = 70 + i * 40;
                    const nivel = sim?.ok ? pinLevel(sim.events, d.pin, t) : 0;
                    return (
                      <g key={`${d.type}-${d.pin}`}>
                        <line x1="170" y1={y} x2="215" y2={y} stroke="var(--border)" strokeWidth="2" />
                        <text x="30" y={y + 4} fontSize="10" fill="var(--muted-foreground)">
                          GPIO {d.pin}
                        </text>
                        {d.type === "led" ? (
                          <>
                            <circle cx="240" cy={y} r="16" fill={d.color ?? "#a3e635"} opacity={0.15 + 0.85 * nivel} />
                            <circle cx="240" cy={y} r="22" fill="none" stroke={d.color ?? "#a3e635"} opacity={nivel * 0.5} strokeWidth="4" />
                            <text x="240" y={y + 34} textAnchor="middle" fontSize="9" fill="var(--muted-foreground)">
                              LED {nivel > 0 ? "ON" : "OFF"}
                            </text>
                          </>
                        ) : d.type === "button" ? (
                          <>
                            <rect x="226" y={y - 12 + (pulsado ? 4 : 0)} width="28" height={pulsado ? 16 : 20} rx="3" fill={pulsado ? "var(--primary)" : "var(--surface)"} stroke="var(--border)" />
                            <text x="240" y={y + 34} textAnchor="middle" fontSize="9" fill="var(--muted-foreground)">
                              {pulsado ? "PRESIONADO" : "suelto"}
                            </text>
                          </>
                        ) : (
                          <>
                            <rect x="224" y={y - 14} width="32" height="28" rx="3" fill="var(--surface)" stroke="var(--border)" />
                            <text x="240" y={y + 4} textAnchor="middle" fontSize="10" fill="var(--primary)">
                              {Math.round(inputs[d.pin] as number)}%
                            </text>
                          </>
                        )}
                      </g>
                    );
                  })}
                </svg>
              </section>

              <section className="panel flex flex-col p-4">
                <p className="label-xs mb-3">Monitor serie</p>
                <pre className="min-h-[150px] flex-1 overflow-auto rounded-sm bg-surface-2 p-3 font-mono text-xs leading-relaxed text-primary">
                  {serialVisible.length ? serialVisible.map((s) => `[${(s.t / 1000).toFixed(1)}s] ${s.text}`).join("\n") : "—"}
                </pre>
              </section>
            </div>

            {sim?.warnings.length ? (
              <ul className="space-y-1 text-xs text-muted-foreground">
                {sim.warnings.map((w) => (
                  <li key={w}>⚠️ {w}</li>
                ))}
              </ul>
            ) : null}

            {sim?.ok && sim.checks ? (
              <section className="panel space-y-2 p-4" aria-live="polite">
                <p className="label-xs">
                  Verificación {sim.passed ? "· ✅ lección superada" : "· pendiente"}
                </p>
                {sim.checks.map((c) => (
                  <p key={c.label} className={`text-sm ${c.ok ? "text-primary" : "text-muted-foreground"}`}>
                    {c.ok ? "✅" : "⬜"} {c.label}
                  </p>
                ))}
              </section>
            ) : null}
          </div>
        </div>
      )}
    </AppShell>
  );
}
