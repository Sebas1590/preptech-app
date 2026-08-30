import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import {
  AREAS,
  DIFICULTADES,
  EMPRESAS,
  PREGUNTAS,
  etiquetaArea,
  etiquetaDificultad,
  type Area,
  type Dificultad,
} from "@/lib/preptech-data";
import { usePrepTech } from "@/lib/preptech-store";

export const Route = createFileRoute("/banco")({
  head: () => ({
    meta: [
      { title: "Banco de preguntas técnicas | PrepTech" },
      {
        name: "description",
        content:
          "Filtra preguntas de algoritmos y diseño de sistemas por empresa, área y nivel de dificultad antes de empezar tu práctica cronometrada.",
      },
      { property: "og:title", content: "Banco de preguntas técnicas | PrepTech" },
      {
        property: "og:description",
        content: "Preguntas clasificadas por empresa, área y dificultad para practicar contra reloj.",
      },
    ],
  }),
  component: Banco,
});

function Chip({
  activo,
  onClick,
  children,
}: {
  activo: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-sm border px-3 py-1.5 font-mono text-[11px] uppercase tracking-wider transition-colors ${
        activo
          ? "border-primary bg-primary text-primary-foreground"
          : "border-border bg-surface-2 text-muted-foreground hover:text-foreground"
      }`}
    >
      {children}
    </button>
  );
}

function Banco() {
  const { estado } = usePrepTech();
  const [empresa, setEmpresa] = useState<string>("todas");
  const [area, setArea] = useState<Area | "todas">("todas");
  const [dificultad, setDificultad] = useState<Dificultad | "todas">("todas");
  const [busqueda, setBusqueda] = useState("");

  const lista = PREGUNTAS.filter(
    (p) =>
      (empresa === "todas" || p.empresa === empresa) &&
      (area === "todas" || p.area === area) &&
      (dificultad === "todas" || p.dificultad === dificultad) &&
      p.titulo.toLowerCase().includes(busqueda.toLowerCase()),
  );

  return (
    <AppShell
      titulo="Banco de preguntas"
      subtitulo="Filtra por empresa, área y nivel de dificultad"
      acciones={
        <span className="font-mono text-xs text-muted-foreground">
          {lista.length} de {PREGUNTAS.length}
        </span>
      }
    >
      <div className="space-y-6">
        <section className="panel space-y-4 p-5">
          <input
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Buscar pregunta…"
            className="w-full rounded-sm border border-input bg-surface-2 px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus:border-primary"
          />
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="label-xs w-20">Empresa</span>
              <Chip activo={empresa === "todas"} onClick={() => setEmpresa("todas")}>
                Todas
              </Chip>
              {EMPRESAS.map((e) => (
                <Chip key={e} activo={empresa === e} onClick={() => setEmpresa(e)}>
                  {e}
                </Chip>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="label-xs w-20">Área</span>
              <Chip activo={area === "todas"} onClick={() => setArea("todas")}>
                Todas
              </Chip>
              {AREAS.map((a) => (
                <Chip key={a.id} activo={area === a.id} onClick={() => setArea(a.id)}>
                  {a.nombre}
                </Chip>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="label-xs w-20">Nivel</span>
              <Chip activo={dificultad === "todas"} onClick={() => setDificultad("todas")}>
                Todos
              </Chip>
              {DIFICULTADES.map((d) => (
                <Chip
                  key={d.id}
                  activo={dificultad === d.id}
                  onClick={() => setDificultad(d.id)}
                >
                  {d.nombre}
                </Chip>
              ))}
            </div>
          </div>
        </section>

        <section className="panel overflow-hidden">
          <ul className="divide-y divide-border">
            {lista.map((p) => {
              const intentos = estado.intentos.filter((i) => i.preguntaId === p.id).length;
              return (
                <li key={p.id}>
                  <Link
                    to="/practica/$preguntaId"
                    params={{ preguntaId: p.id }}
                    className="flex items-center gap-4 px-5 py-4 transition-colors hover:bg-surface-2"
                  >
                    <span
                      className={`shrink-0 rounded-sm px-2 py-1 font-mono text-[10px] uppercase tracking-wider ${
                        p.dificultad === "facil"
                          ? "bg-primary/15 text-primary"
                          : p.dificultad === "medio"
                            ? "bg-warn/15 text-warn"
                            : "bg-signal/15 text-signal"
                      }`}
                    >
                      {etiquetaDificultad[p.dificultad]}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{p.titulo}</p>
                      <p className="font-mono text-[11px] text-muted-foreground">
                        {p.empresa} · {etiquetaArea[p.area]} · objetivo {p.minutosObjetivo} min
                      </p>
                    </div>
                    <span className="shrink-0 font-mono text-[11px] text-muted-foreground">
                      {intentos} intentos
                    </span>
                  </Link>
                </li>
              );
            })}
            {lista.length === 0 ? (
              <li className="px-5 py-10 text-center text-sm text-muted-foreground">
                No hay preguntas con esos filtros.
              </li>
            ) : null}
          </ul>
        </section>
      </div>
    </AppShell>
  );
}
