import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { CONDUCTUALES } from "@/lib/preptech-data";
import { formatearTiempo, usePrepTech } from "@/lib/preptech-store";

export const Route = createFileRoute("/conductual")({
  head: () => ({
    meta: [
      { title: "Simulador de entrevista conductual | PrepTech" },
      {
        name: "description",
        content:
          "Practica en voz alta preguntas de comportamiento, graba tu respuesta y estructúrala con el método STAR.",
      },
      { property: "og:title", content: "Simulador de entrevista conductual | PrepTech" },
      {
        property: "og:description",
        content: "Grabación de audio, cronómetro y guía STAR para respuestas ordenadas.",
      },
    ],
  }),
  component: Conductual,
});

function Conductual() {
  const { estado, registrarGrabacion } = usePrepTech();
  const [indice, setIndice] = useState(0);
  const [grabando, setGrabando] = useState(false);
  const [segundos, setSegundos] = useState(0);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notas, setNotas] = useState("");
  const [pasoStar, setPasoStar] = useState(0);
  const recorder = useRef<MediaRecorder | null>(null);
  const chunks = useRef<BlobPart[]>([]);

  const actual = CONDUCTUALES[indice];

  useEffect(() => {
    if (!grabando) return;
    const t = setInterval(() => setSegundos((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [grabando]);

  const iniciar = async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunks.current = [];
      const mr = new MediaRecorder(stream);
      mr.ondataavailable = (e) => chunks.current.push(e.data);
      mr.onstop = () => {
        const blob = new Blob(chunks.current, { type: "audio/webm" });
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      recorder.current = mr;
      setSegundos(0);
      setAudioUrl(null);
      setPasoStar(0);
      setGrabando(true);
    } catch {
      setError("No se pudo acceder al micrófono. Revisa los permisos del navegador.");
    }
  };

  const detener = () => {
    recorder.current?.stop();
    setGrabando(false);
  };

  const guardar = () => {
    registrarGrabacion({
      preguntaId: actual.id,
      pregunta: actual.pregunta,
      segundos,
      notas,
    });
    setNotas("");
    setAudioUrl(null);
    setSegundos(0);
  };

  return (
    <AppShell
      titulo="Simulador conductual"
      subtitulo="Responde en voz alta y estructura con el método STAR"
      acciones={
        <span className="font-mono text-xs text-muted-foreground">
          {estado.grabaciones.length} simulacros guardados
        </span>
      }
    >
      <div className="grid gap-6 lg:grid-cols-5">
        <section className="panel space-y-5 p-6 lg:col-span-3">
          <div className="flex items-center gap-2">
            <span className="label-xs">
              Pregunta {indice + 1}/{CONDUCTUALES.length}
            </span>
            <span className="rounded-sm bg-surface-2 px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
              {actual.empresa}
            </span>
          </div>
          <h2 className="text-2xl font-semibold leading-snug">{actual.pregunta}</h2>
          <p className="font-mono text-[11px] text-muted-foreground">
            Competencia evaluada: {actual.competencia}
          </p>

          <div className="rounded-sm border border-border bg-surface-2 p-4">
            <div className="flex items-center gap-4">
              <button
                onClick={grabando ? detener : iniciar}
                className={`grid size-12 place-items-center rounded-full ${
                  grabando ? "bg-signal" : "bg-primary"
                }`}
                aria-label={grabando ? "Detener grabación" : "Iniciar grabación"}
              >
                <span
                  className={
                    grabando
                      ? "size-4 rounded-[2px] bg-signal-foreground"
                      : "size-4 rounded-full bg-primary-foreground"
                  }
                />
              </button>
              <div className="flex-1">
                <p className="font-mono text-lg">{formatearTiempo(segundos)}</p>
                <p className="text-xs text-muted-foreground">
                  {grabando ? "Grabando tu respuesta…" : "Pulsa para grabar (objetivo: 2 min)"}
                </p>
              </div>
              <div className="flex h-8 items-end gap-1">
                {[40, 70, 100, 60, 85, 45, 75].map((h, i) => (
                  <span
                    key={i}
                    className={`w-1.5 rounded-full ${grabando ? "bg-signal" : "bg-border"}`}
                    style={{ height: `${grabando ? h : 25}%` }}
                  />
                ))}
              </div>
            </div>

            {error ? <p className="mt-3 text-xs text-destructive">{error}</p> : null}

            {audioUrl ? (
              <div className="mt-4 space-y-3">
                <audio controls src={audioUrl} className="w-full" />
                <textarea
                  value={notas}
                  onChange={(e) => setNotas(e.target.value)}
                  placeholder="Retroalimentación: ¿cerraste con un resultado medible?"
                  className="h-20 w-full resize-none rounded-sm border border-input bg-background p-3 text-sm outline-none placeholder:text-muted-foreground focus:border-primary"
                />
                <button
                  onClick={guardar}
                  className="rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
                >
                  Guardar simulacro
                </button>
              </div>
            ) : null}
          </div>

          <button
            onClick={() => {
              setIndice((i) => (i + 1) % CONDUCTUALES.length);
              setAudioUrl(null);
              setSegundos(0);
              setPasoStar(0);
            }}
            className="rounded-sm border border-border bg-surface-2 px-4 py-2 text-sm"
          >
            Siguiente pregunta
          </button>
        </section>

        <div className="space-y-6 lg:col-span-2">
          <section className="panel p-5">
            <p className="label-xs">Guía STAR</p>
            <ul className="mt-4 space-y-2">
              {actual.guiaStar.map((paso, idx) => (
                <li key={paso.letra}>
                  <button
                    onClick={() => setPasoStar(idx)}
                    className={`flex w-full items-start gap-3 rounded-sm border px-3 py-2.5 text-left transition-colors ${
                      idx === pasoStar
                        ? "border-primary bg-primary/10"
                        : "border-border bg-surface-2"
                    }`}
                  >
                    <span
                      className={`grid size-6 shrink-0 place-items-center rounded-sm font-mono text-[11px] font-bold ${
                        idx <= pasoStar
                          ? "bg-primary text-primary-foreground"
                          : "bg-border text-muted-foreground"
                      }`}
                    >
                      {paso.letra}
                    </span>
                    <span>
                      <span className="block text-sm font-medium">{paso.nombre}</span>
                      <span className="block text-xs text-muted-foreground">{paso.ayuda}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <section className="panel p-5">
            <p className="label-xs">Simulacros recientes</p>
            {estado.grabaciones.length === 0 ? (
              <p className="mt-3 text-sm text-muted-foreground">
                Aún no has guardado ninguna respuesta.
              </p>
            ) : (
              <ul className="mt-3 divide-y divide-border">
                {estado.grabaciones.slice(0, 5).map((g) => (
                  <li key={g.id} className="py-2.5">
                    <p className="truncate text-sm">{g.pregunta}</p>
                    <p className="font-mono text-[11px] text-muted-foreground">
                      {formatearTiempo(g.segundos)} · {new Date(g.fecha).toLocaleDateString("es-PE")}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </AppShell>
  );
}
