import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { PREGUNTAS, etiquetaArea, etiquetaDificultad } from "@/lib/preptech-data";
import { formatearTiempo, usePrepTech } from "@/lib/preptech-store";

export const Route = createFileRoute("/practica/$preguntaId")({
  head: () => ({
    meta: [
      { title: "Práctica cronometrada | PrepTech" },
      {
        name: "description",
        content:
          "Resuelve la pregunta con el editor integrado, cronómetro en marcha y registro automático de tu intento.",
      },
      { property: "og:title", content: "Práctica cronometrada | PrepTech" },
      {
        property: "og:description",
        content: "Editor, cronómetro y pistas graduales para practicar como en la entrevista real.",
      },
    ],
  }),
  component: Practica,
});

function Practica() {
  const { preguntaId } = Route.useParams();
  const navigate = useNavigate();
  const { registrarIntento } = usePrepTech();
  const pregunta = useMemo(() => PREGUNTAS.find((p) => p.id === preguntaId), [preguntaId]);

  const [segundos, setSegundos] = useState(0);
  const [corriendo, setCorriendo] = useState(true);
  const [codigo, setCodigo] = useState(pregunta?.plantilla ?? "");
  const [pistasVisibles, setPistasVisibles] = useState(0);
  const [notas, setNotas] = useState("");
  const intervalo = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!corriendo) return;
    intervalo.current = setInterval(() => setSegundos((s) => s + 1), 1000);
    return () => {
      if (intervalo.current) clearInterval(intervalo.current);
    };
  }, [corriendo]);

  if (!pregunta) {
    return (
      <AppShell titulo="Pregunta no encontrada">
        <Link to="/banco" className="text-sm text-primary underline">
          Volver al banco
        </Link>
      </AppShell>
    );
  }

  const limite = pregunta.minutosObjetivo * 60;
  const excedido = segundos > limite;

  const finalizar = (resultado: "resuelto" | "parcial" | "sin-resolver") => {
    registrarIntento({
      preguntaId: pregunta.id,
      titulo: pregunta.titulo,
      area: pregunta.area,
      dificultad: pregunta.dificultad,
      empresa: pregunta.empresa,
      segundos,
      resultado,
      notas,
    });
    navigate({ to: "/" });
  };

  return (
    <AppShell
      titulo={pregunta.titulo}
      subtitulo={`${pregunta.empresa} · ${etiquetaArea[pregunta.area]} · ${etiquetaDificultad[pregunta.dificultad]}`}
      acciones={
        <div className="flex items-center gap-3">
          <div
            className={`flex items-center gap-2 rounded-sm border px-3 py-1.5 font-mono text-sm ${
              excedido ? "border-signal text-signal" : "border-border text-primary"
            }`}
          >
            <span
              className={`size-2 rounded-full ${corriendo ? "bg-primary" : "bg-muted-foreground"}`}
            />
            {formatearTiempo(segundos)}
            <span className="text-muted-foreground">/ {pregunta.minutosObjetivo}:00</span>
          </div>
          <button
            onClick={() => setCorriendo((c) => !c)}
            className="rounded-sm border border-border bg-surface-2 px-3 py-1.5 text-sm"
          >
            {corriendo ? "Pausar" : "Reanudar"}
          </button>
        </div>
      }
    >
      <div className="grid gap-6 lg:grid-cols-5">
        <section className="panel space-y-5 p-5 lg:col-span-2">
          <div>
            <p className="label-xs">Enunciado</p>
            <p className="mt-2 text-sm leading-relaxed text-foreground/85">{pregunta.enunciado}</p>
          </div>

          {pregunta.ejemplo ? (
            <div className="rounded-sm border border-border bg-surface-2 p-3 font-mono text-xs leading-relaxed">
              <p className="text-muted-foreground">// entrada</p>
              <p>{pregunta.ejemplo.entrada}</p>
              <p className="mt-2 text-muted-foreground">// salida</p>
              <p className="text-primary">{pregunta.ejemplo.salida}</p>
            </div>
          ) : null}

          <div>
            <div className="flex items-center justify-between">
              <p className="label-xs">Pistas</p>
              <button
                onClick={() => setPistasVisibles((n) => Math.min(pregunta.pistas.length, n + 1))}
                disabled={pistasVisibles >= pregunta.pistas.length}
                className="font-mono text-[11px] text-primary disabled:text-muted-foreground"
              >
                Revelar ({pistasVisibles}/{pregunta.pistas.length})
              </button>
            </div>
            <ul className="mt-3 space-y-2">
              {pregunta.pistas.slice(0, pistasVisibles).map((p, idx) => (
                <li
                  key={idx}
                  className="rounded-sm border border-border bg-surface-2 px-3 py-2 text-xs text-foreground/80"
                >
                  {p}
                </li>
              ))}
              {pistasVisibles === 0 ? (
                <li className="text-xs text-muted-foreground">
                  Intenta al menos 5 minutos antes de revelar una pista.
                </li>
              ) : null}
            </ul>
          </div>
        </section>

        <section className="panel flex flex-col overflow-hidden lg:col-span-3">
          <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
            <span className="font-mono text-[11px] text-muted-foreground">
              {pregunta.area === "sistemas" ? "diseño.md" : "solucion.py"}
            </span>
            <span className="font-mono text-[11px] text-muted-foreground">
              {codigo.split("\n").length} líneas
            </span>
          </div>
          <textarea
            value={codigo}
            onChange={(e) => setCodigo(e.target.value)}
            spellCheck={false}
            className="min-h-[380px] flex-1 resize-none bg-surface-2 p-4 font-mono text-[13px] leading-relaxed outline-none"
          />
          <div className="space-y-3 border-t border-border p-4">
            <textarea
              value={notas}
              onChange={(e) => setNotas(e.target.value)}
              placeholder="Retroalimentación: qué te costó, qué repasar…"
              className="h-20 w-full resize-none rounded-sm border border-input bg-surface-2 p-3 text-sm outline-none placeholder:text-muted-foreground focus:border-primary"
            />
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => finalizar("resuelto")}
                className="rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
              >
                Marcar resuelta
              </button>
              <button
                onClick={() => finalizar("parcial")}
                className="rounded-sm border border-border bg-surface-2 px-4 py-2 text-sm"
              >
                Resuelta a medias
              </button>
              <button
                onClick={() => finalizar("sin-resolver")}
                className="rounded-sm border border-border bg-surface-2 px-4 py-2 text-sm text-muted-foreground"
              >
                No la logré
              </button>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
