import { useCallback, useEffect, useState } from "react";
import type { Area, Dificultad } from "./preptech-data";

export type RevisionIA = {
  score: number;
  correctness: "correcto" | "parcial" | "incorrecto" | "sin_intento";
  strength: string;
  improvements: string[];
  complexity: string;
  next_step: string;
};

export type Intento = {
  id: string;
  preguntaId: string;
  titulo: string;
  area: Area;
  dificultad: Dificultad;
  empresa: string;
  segundos: number;
  resultado: "resuelto" | "parcial" | "sin-resolver";
  fecha: string;
  notas?: string;
  feedbackIA?: RevisionIA;
};

export type GrabacionConductual = {
  id: string;
  preguntaId: string;
  pregunta: string;
  segundos: number;
  fecha: string;
  notas: string;
};

export type Perfil = {
  nombre: string;
  empresaObjetivo: string;
  fechaEntrevista: string;
  metaSemanal: number;
};

export type EstadoPrepTech = {
  perfil: Perfil;
  intentos: Intento[];
  grabaciones: GrabacionConductual[];
};

const CLAVE = "preptech:v1";

function fechaObjetivoPorDefecto() {
  const d = new Date();
  d.setDate(d.getDate() + 21);
  return d.toISOString().slice(0, 10);
}

export const estadoInicial: EstadoPrepTech = {
  perfil: {
    nombre: "Postulante",
    empresaObjetivo: "Google",
    fechaEntrevista: fechaObjetivoPorDefecto(),
    metaSemanal: 15,
  },
  intentos: [],
  grabaciones: [],
};

type Escucha = (estado: EstadoPrepTech) => void;
let memoria: EstadoPrepTech | null = null;
const escuchas = new Set<Escucha>();

function leer(): EstadoPrepTech {
  if (memoria) return memoria;
  if (typeof window === "undefined") return estadoInicial;
  try {
    const crudo = window.localStorage.getItem(CLAVE);
    memoria = crudo ? { ...estadoInicial, ...JSON.parse(crudo) } : estadoInicial;
  } catch {
    memoria = estadoInicial;
  }
  return memoria;
}

function escribir(siguiente: EstadoPrepTech) {
  memoria = siguiente;
  try {
    window.localStorage.setItem(CLAVE, JSON.stringify(siguiente));
  } catch {
    /* almacenamiento no disponible */
  }
  escuchas.forEach((fn) => fn(siguiente));
}

export function usePrepTech() {
  const [estado, setEstado] = useState<EstadoPrepTech>(estadoInicial);
  const [listo, setListo] = useState(false);

  useEffect(() => {
    setEstado(leer());
    setListo(true);
    const fn: Escucha = (s) => setEstado(s);
    escuchas.add(fn);
    return () => {
      escuchas.delete(fn);
    };
  }, []);

  const actualizarPerfil = useCallback((parcial: Partial<Perfil>) => {
    const actual = leer();
    escribir({ ...actual, perfil: { ...actual.perfil, ...parcial } });
  }, []);

  const registrarIntento = useCallback((intento: Omit<Intento, "id" | "fecha">) => {
    const actual = leer();
    escribir({
      ...actual,
      intentos: [
        { ...intento, id: crypto.randomUUID(), fecha: new Date().toISOString() },
        ...actual.intentos,
      ],
    });
  }, []);

  const registrarGrabacion = useCallback((g: Omit<GrabacionConductual, "id" | "fecha">) => {
    const actual = leer();
    escribir({
      ...actual,
      grabaciones: [
        { ...g, id: crypto.randomUUID(), fecha: new Date().toISOString() },
        ...actual.grabaciones,
      ],
    });
  }, []);

  const reiniciar = useCallback(() => escribir(estadoInicial), []);

  return { estado, listo, actualizarPerfil, registrarIntento, registrarGrabacion, reiniciar };
}

export function formatearTiempo(segundos: number) {
  const m = Math.floor(segundos / 60);
  const s = segundos % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function diasRestantes(fechaISO: string) {
  const objetivo = new Date(`${fechaISO}T00:00:00`);
  const hoy = new Date();
  hoy.setHours(0, 0, 0, 0);
  return Math.max(0, Math.round((objetivo.getTime() - hoy.getTime()) / 86400000));
}

export function metricas(intentos: Intento[]) {
  const resueltos = intentos.filter((i) => i.resultado === "resuelto");
  const promedio = intentos.length
    ? Math.round(intentos.reduce((a, i) => a + i.segundos, 0) / intentos.length)
    : 0;
  const porArea = new Map<Area, { total: number; resueltos: number }>();
  intentos.forEach((i) => {
    const prev = porArea.get(i.area) ?? { total: 0, resueltos: 0 };
    porArea.set(i.area, {
      total: prev.total + 1,
      resueltos: prev.resueltos + (i.resultado === "resuelto" ? 1 : 0),
    });
  });
  const debiles = [...porArea.entries()]
    .map(([area, v]) => ({ area, ratio: v.total ? v.resueltos / v.total : 0, total: v.total }))
    .sort((a, b) => a.ratio - b.ratio);

  const semana = intentos.filter(
    (i) => Date.now() - new Date(i.fecha).getTime() < 7 * 86400000,
  ).length;

  return { total: intentos.length, resueltos: resueltos.length, promedio, debiles, semana };
}
