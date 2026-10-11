import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { usePrepTech } from "@/lib/preptech-store";

export const Route = createFileRoute("/perfil")({
  head: () => ({
    meta: [
      { title: "Perfil y meta | PrepTech" },
      { name: "description", content: "Configura tu empresa objetivo, fecha de entrevista y meta semanal." },
    ],
  }),
  component: Perfil,
});

function Perfil() {
  const { estado, actualizarPerfil, reiniciar } = usePrepTech();
  const { perfil } = estado;
  const campo =
    "mt-2 w-full rounded-sm border border-input bg-surface-2 p-3 text-sm outline-none focus:border-primary";

  return (
    <AppShell titulo="Perfil y meta" subtitulo="Se guarda en este navegador">
      <section className="panel max-w-xl space-y-5 p-5">
        <label className="block">
          <span className="label-xs">Nombre</span>
          <input
            className={campo}
            value={perfil.nombre}
            onChange={(e) => actualizarPerfil({ nombre: e.target.value })}
          />
        </label>
        <label className="block">
          <span className="label-xs">Empresa objetivo</span>
          <input
            className={campo}
            value={perfil.empresaObjetivo}
            onChange={(e) => actualizarPerfil({ empresaObjetivo: e.target.value })}
          />
        </label>
        <label className="block">
          <span className="label-xs">Fecha de la entrevista</span>
          <input
            type="date"
            className={campo}
            value={perfil.fechaEntrevista}
            onChange={(e) => e.target.value && actualizarPerfil({ fechaEntrevista: e.target.value })}
          />
        </label>
        <label className="block">
          <span className="label-xs">Meta semanal (preguntas)</span>
          <input
            type="number"
            min={1}
            className={campo}
            value={perfil.metaSemanal}
            onChange={(e) => actualizarPerfil({ metaSemanal: Math.max(1, Number(e.target.value) || 1) })}
          />
        </label>
        <button
          onClick={() => confirm("¿Borrar todo tu progreso?") && reiniciar()}
          className="rounded-sm border border-border bg-surface-2 px-4 py-2 text-sm text-muted-foreground"
        >
          Reiniciar progreso
        </button>
      </section>
    </AppShell>
  );
}
