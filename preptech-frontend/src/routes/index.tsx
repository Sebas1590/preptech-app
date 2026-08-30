import { createFileRoute, Link } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { PREGUNTAS, etiquetaArea, etiquetaDificultad } from "@/lib/preptech-data";
import {
  diasRestantes,
  formatearTiempo,
  metricas,
  usePrepTech,
} from "@/lib/preptech-store";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "PrepTech — Panel de preparación para entrevistas técnicas" },
      {
        name: "description",
        content:
          "Panel de PrepTech: cuenta regresiva a tu entrevista, progreso de práctica, tiempos de resolución y áreas débiles en un solo lugar.",
      },
      { property: "og:title", content: "PrepTech — Panel de preparación" },
      {
        property: "og:description",
        content:
          "Centraliza tu práctica de algoritmos, diseño de sistemas y entrevistas de comportamiento con seguimiento real del avance.",
      },
    ],
  }),
  component: Panel,
});

function Metrica({
  etiqueta,
  valor,
  nota,
  acento,
}: {
  etiqueta: string;
  valor: string;
  nota: string;
  acento?: boolean;
}) {
  return (
    <div className="panel p-5">
      <p className="label-xs">{etiqueta}</p>
      <p
        className={`mt-3 font-mono text-3xl font-semibold ${acento ? "text-primary" : "text-foreground"}`}
      >
        {valor}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">{nota}</p>
    </div>
  );
}

function Panel() {
  const { estado, listo } = usePrepTech();
  const m = metricas(estado.intentos);
  const dias = diasRestantes(estado.perfil.fechaEntrevista);
  const avanceMeta = Math.min(100, Math.round((m.semana / estado.perfil.metaSemanal) * 100));
  const recomendadas = PREGUNTAS.filter(
    (p) => !estado.intentos.some((i) => i.preguntaId === p.id && i.resultado === "resuelto"),
  ).slice(0, 3);

  return (
    <AppShell
      titulo="Panel de progreso"
      subtitulo={`${estado.perfil.nombre} · objetivo ${estado.perfil.empresaObjetivo}`}
      acciones={
        <Link
          to="/banco"
          className="rounded-sm bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
        >
          Iniciar práctica
        </Link>
      }
    >
      <div className="space-y-6">
        <section className="panel flex flex-wrap items-end justify-between gap-6 p-6">
          <div>
            <p className="label-xs">Cuenta regresiva</p>
            <p className="mt-2 font-display text-5xl font-semibold leading-none">
              {dias} <span className="text-2xl text-muted-foreground">días</span>
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              {estado.perfil.empresaObjetivo} · entrevista el {estado.perfil.fechaEntrevista}
            </p>
          </div>
          <div className="w-full max-w-xs">
            <div className="flex items-center justify-between">
              <span className="label-xs">Meta semanal</span>
              <span className="font-mono text-xs text-primary">
                {m.semana}/{estado.perfil.metaSemanal}
              </span>
            </div>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface-2">
              <div className="h-full bg-primary" style={{ width: `${avanceMeta}%` }} />
            </div>
          </div>
        </section>

        <section className="grid gap-5 sm:grid-cols-2 xl:grid-cols-4">
          <Metrica
            etiqueta="Preguntas resueltas"
            valor={String(m.resueltos)}
            nota={`${m.total} intentos registrados`}
            acento
          />
          <Metrica
            etiqueta="Tiempo promedio"
            valor={m.promedio ? formatearTiempo(m.promedio) : "--:--"}
            nota="por intento cronometrado"
          />
          <Metrica
            etiqueta="Esta semana"
            valor={String(m.semana)}
            nota="sesiones de práctica"
          />
          <Metrica
            etiqueta="Simulacros conductuales"
            valor={String(estado.grabaciones.length)}
            nota="respuestas grabadas con método STAR"
          />
        </section>

        <div className="grid gap-6 lg:grid-cols-5">
          <section className="panel lg:col-span-3">
            <div className="flex items-center justify-between border-b border-border px-5 py-3">
              <h2 className="text-sm font-semibold">Historial de intentos</h2>
              <span className="font-mono text-[11px] text-muted-foreground">
                {estado.intentos.length} registros
              </span>
            </div>
            {!listo || estado.intentos.length === 0 ? (
              <p className="px-5 py-10 text-center text-sm text-muted-foreground">
                Aún no hay intentos. Resuelve tu primera pregunta desde el banco.
              </p>
            ) : (
              <ul className="divide-y divide-border">
                {estado.intentos.slice(0, 7).map((i) => (
                  <li key={i.id} className="flex items-center gap-3 px-5 py-3">
                    <span
                      className={`size-2.5 shrink-0 rounded-full ${
                        i.resultado === "resuelto"
                          ? "bg-primary"
                          : i.resultado === "parcial"
                            ? "bg-warn"
                            : "bg-signal"
                      }`}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{i.titulo}</p>
                      <p className="font-mono text-[11px] text-muted-foreground">
                        {i.empresa} · {etiquetaArea[i.area]} · {etiquetaDificultad[i.dificultad]}
                      </p>
                    </div>
                    <span className="font-mono text-xs text-muted-foreground">
                      {formatearTiempo(i.segundos)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <div className="space-y-6 lg:col-span-2">
            <section className="panel p-5">
              <h2 className="text-sm font-semibold">Áreas débiles</h2>
              {m.debiles.length === 0 ? (
                <p className="mt-3 text-sm text-muted-foreground">
                  Se calculan después de tu primer intento.
                </p>
              ) : (
                <ul className="mt-4 space-y-3">
                  {m.debiles.map((d) => (
                    <li key={d.area}>
                      <div className="flex items-center justify-between text-sm">
                        <span>{etiquetaArea[d.area]}</span>
                        <span className="font-mono text-xs text-muted-foreground">
                          {Math.round(d.ratio * 100)}% · {d.total}
                        </span>
                      </div>
                      <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-2">
                        <div
                          className="h-full bg-info"
                          style={{ width: `${Math.round(d.ratio * 100)}%` }}
                        />
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="panel p-5">
              <h2 className="text-sm font-semibold">Siguientes recomendadas</h2>
              <ul className="mt-4 space-y-2">
                {recomendadas.map((p) => (
                  <li key={p.id}>
                    <Link
                      to="/practica/$preguntaId"
                      params={{ preguntaId: p.id }}
                      className="block rounded-sm border border-border bg-surface-2 px-3 py-2.5 transition-colors hover:border-primary"
                    >
                      <p className="text-sm font-medium">{p.titulo}</p>
                      <p className="font-mono text-[11px] text-muted-foreground">
                        {p.empresa} · {etiquetaDificultad[p.dificultad]} · {p.minutosObjetivo} min
                      </p>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
