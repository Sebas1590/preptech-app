import { Link, useRouterState } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { usePrepTech, diasRestantes } from "@/lib/preptech-store";
import { useAiStatus } from "@/lib/api";

const NAV = [
  { to: "/", num: "01", label: "Panel" },
  { to: "/banco", num: "02", label: "Banco de preguntas" },
  { to: "/conductual", num: "03", label: "Simulador conductual" },
  { to: "/coach", num: "04", label: "Coach IA" },
  { to: "/iot", num: "05", label: "Módulo IoT" },
  { to: "/ia", num: "06", label: "Configuración de IA" },
  { to: "/perfil", num: "07", label: "Perfil y meta" },
] as const;

export function AppShell({
  titulo,
  subtitulo,
  acciones,
  children,
}: {
  titulo: string;
  subtitulo?: string;
  acciones?: ReactNode;
  children: ReactNode;
}) {
  const { estado } = usePrepTech();
  const { status, offline } = useAiStatus();
  const path = useRouterState({ select: (s) => s.location.pathname });
  const dias = diasRestantes(estado.perfil.fechaEntrevista);

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-border bg-surface md:flex">
        <div className="flex items-center gap-3 border-b border-border px-5 py-5">
          <div className="grid size-9 place-items-center rounded-sm bg-primary font-display text-lg font-bold text-primary-foreground">
            P
          </div>
          <div>
            <p className="font-display text-base font-semibold leading-none">PrepTech</p>
            <p className="label-xs mt-1">Consola de práctica</p>
          </div>
        </div>

        <nav className="flex flex-col gap-1 p-3">
          {NAV.map((item) => {
            const activo = item.to === "/" ? path === "/" : path.startsWith(item.to);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`flex items-center justify-between rounded-sm px-3 py-2.5 text-sm transition-colors ${
                  activo
                    ? "bg-primary font-semibold text-primary-foreground"
                    : "text-muted-foreground hover:bg-surface-2 hover:text-foreground"
                }`}
              >
                <span>{item.label}</span>
                <span className="font-mono text-[10px] opacity-60">{item.num}</span>
              </Link>
            );
          })}
        </nav>

        <div className="mt-auto space-y-3 p-3">
          <Link
            to="/ia"
            className="flex items-center gap-2 rounded-sm border border-border bg-surface-2 px-3 py-2 text-xs"
          >
            <span
              className={`size-2 rounded-full ${offline ? "bg-signal" : status?.connected ? "bg-primary" : "bg-muted-foreground"}`}
            />
            {offline ? "API sin conexión" : status?.connected ? `IA conectada · ${status.model}` : "IA desconectada"}
          </Link>
          <div className="rounded-sm border border-border bg-surface-2 p-4">
            <p className="label-xs">Entrevista objetivo</p>
            <p className="mt-2 font-display text-3xl font-semibold text-primary">{dias} días</p>
            <p className="mt-1 font-mono text-[11px] text-muted-foreground">
              {estado.perfil.empresaObjetivo} · {estado.perfil.fechaEntrevista}
            </p>
          </div>
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <header className="sticky top-0 z-10 flex flex-wrap items-center gap-4 border-b border-border bg-background/90 px-6 py-4 backdrop-blur">
          <div className="min-w-0">
            <h1 className="truncate text-xl font-semibold">{titulo}</h1>
            {subtitulo ? (
              <p className="mt-0.5 text-sm text-muted-foreground">{subtitulo}</p>
            ) : null}
          </div>
          <div className="ml-auto flex items-center gap-3">{acciones}</div>
        </header>
        <main className="grid-noise min-h-[calc(100vh-73px)] p-6">{children}</main>
      </div>
    </div>
  );
}
