import { createFileRoute, Link } from "@tanstack/react-router";
import { useRef, useState, useEffect } from "react";
import { AppShell } from "@/components/AppShell";
import { api, useAiStatus } from "@/lib/api";
import { usePrepTech } from "@/lib/preptech-store";

export const Route = createFileRoute("/coach")({
  head: () => ({
    meta: [
      { title: "Coach IA | PrepTech" },
      { name: "description", content: "Chatea con el Coach PrepTech: pistas, progreso y análisis STAR." },
    ],
  }),
  component: Coach,
});

type Mensaje = { role: "user" | "assistant"; content: string; tools?: { name: string; source?: string }[] | undefined };
type Area = "algoritmos" | "sistemas" | "comportamiento";
const AREAS: { id: Area; label: string }[] = [
  { id: "algoritmos", label: "Algoritmos" },
  { id: "sistemas", label: "System Design" },
  { id: "comportamiento", label: "Behavioral" },
];
const ATAJOS = [
  "Recomiéndame preguntas para practicar según mi empresa objetivo.",
  "Muéstrame mi progreso de las últimas semanas.",
  "¿Cuántos días me faltan para mi entrevista y qué ritmo debo llevar?",
];

function Coach() {
  const { estado } = usePrepTech();
  const { status, offline } = useAiStatus();
  const [area, setArea] = useState<Area>("algoritmos");
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fin = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fin.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, enviando]);

  const enviar = async (mensaje: string) => {
    const m = mensaje.trim();
    if (!m || enviando) return;
    setError(null);
    setEnviando(true);
    const historial = mensajes.map(({ role, content }) => ({ role, content }));
    setMensajes((p) => [...p, { role: "user", content: m }]);
    setTexto("");
    try {
      const r = await api<{ text: string; tools: Mensaje["tools"] }>("/coach/chat", {
        method: "POST",
        json: { message: m, area, history: historial, perfil: estado.perfil, progreso: { intentos: estado.intentos } },
      });
      setMensajes((p) => [...p, { role: "assistant", content: r.text, tools: r.tools }]);
    } catch (e) {
      setMensajes((p) => p.slice(0, -1));
      setTexto(m);
      setError(e instanceof Error ? e.message : "Error inesperado");
    } finally {
      setEnviando(false);
    }
  };

  const bloqueado = offline || !status?.configured;

  return (
    <AppShell titulo="Coach IA" subtitulo="Pistas graduales, progreso real y análisis STAR">
      <div className="mx-auto flex max-w-3xl flex-col gap-4">
        {bloqueado ? (
          <p className="panel p-4 text-sm">
            {offline ? "El backend no responde. " : "La IA no está conectada. "}
            <Link to="/ia" className="text-primary underline">
              Ir a Configuración de IA
            </Link>
          </p>
        ) : null}

        <div className="flex flex-wrap gap-2">
          {AREAS.map((a) => (
            <button
              key={a.id}
              onClick={() => setArea(a.id)}
              className={`rounded-sm border px-3 py-1.5 text-sm ${
                area === a.id ? "border-primary bg-primary text-primary-foreground" : "border-border bg-surface-2"
              }`}
            >
              {a.label}
            </button>
          ))}
        </div>

        <section className="panel min-h-[420px] space-y-4 p-4" aria-live="polite">
          {mensajes.length === 0 ? (
            <div className="space-y-3 text-sm text-muted-foreground">
              <p>Hola, soy tu Coach PrepTech. Pídeme un ejercicio, una pista o pega tu respuesta conductual.</p>
              <div className="flex flex-wrap gap-2">
                {ATAJOS.map((a) => (
                  <button
                    key={a}
                    disabled={bloqueado}
                    onClick={() => enviar(a)}
                    className="rounded-sm border border-border bg-surface-2 px-3 py-1.5 text-left text-xs text-foreground disabled:opacity-40"
                  >
                    {a}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
          {mensajes.map((m, i) => (
            <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div
                className={`max-w-[85%] whitespace-pre-wrap rounded-sm px-3 py-2 text-sm leading-relaxed ${
                  m.role === "user" ? "bg-primary text-primary-foreground" : "border border-border bg-surface-2"
                }`}
              >
                {m.content}
                {m.tools?.length ? (
                  <p className="mt-2 font-mono text-[10px] text-muted-foreground">
                    🔧 {m.tools.map((t) => `${t.name}${t.source ? ` (${t.source})` : ""}`).join(" · ")}
                  </p>
                ) : null}
              </div>
            </div>
          ))}
          {enviando ? <p className="font-mono text-xs text-muted-foreground">Pensando…</p> : null}
          <div ref={fin} />
        </section>

        {error ? (
          <p role="alert" className="rounded-sm border border-signal px-3 py-2 text-sm text-signal">
            {error}
          </p>
        ) : null}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            void enviar(texto);
          }}
          className="flex gap-2"
        >
          <textarea
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void enviar(texto);
              }
            }}
            maxLength={2000}
            rows={2}
            placeholder="Escribe tu mensaje…"
            className="flex-1 resize-none rounded-sm border border-input bg-surface-2 p-3 text-sm outline-none focus:border-primary"
          />
          <button
            type="submit"
            disabled={bloqueado || enviando || !texto.trim()}
            className="rounded-sm bg-primary px-5 text-sm font-semibold text-primary-foreground disabled:opacity-40"
          >
            Enviar
          </button>
        </form>
        <p className="text-center text-[11px] text-muted-foreground">
          Práctica orientativa: la nota del coach no predice una contratación.
        </p>
      </div>
    </AppShell>
  );
}
