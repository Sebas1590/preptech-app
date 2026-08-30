export type Area = "algoritmos" | "sistemas" | "comportamiento";
export type Dificultad = "facil" | "medio" | "dificil";

export type Pregunta = {
  id: string;
  titulo: string;
  empresa: string;
  area: Area;
  dificultad: Dificultad;
  minutosObjetivo: number;
  enunciado: string;
  ejemplo?: { entrada: string; salida: string };
  pistas: string[];
  plantilla: string;
};

export type PreguntaConductual = {
  id: string;
  pregunta: string;
  empresa: string;
  competencia: string;
  guiaStar: { letra: string; nombre: string; ayuda: string }[];
};

export const EMPRESAS = ["Google", "Amazon", "Meta", "Anthropic", "Microsoft"] as const;

export const AREAS: { id: Area; nombre: string }[] = [
  { id: "algoritmos", nombre: "Algoritmos" },
  { id: "sistemas", nombre: "Diseño de sistemas" },
  { id: "comportamiento", nombre: "Comportamiento" },
];

export const DIFICULTADES: { id: Dificultad; nombre: string }[] = [
  { id: "facil", nombre: "Fácil" },
  { id: "medio", nombre: "Medio" },
  { id: "dificil", nombre: "Difícil" },
];

const guiaStarBase = [
  { letra: "S", nombre: "Situación", ayuda: "Contexto en 2 frases: dónde, cuándo, con quién." },
  { letra: "T", nombre: "Tarea", ayuda: "Cuál era tu responsabilidad concreta." },
  { letra: "A", nombre: "Acción", ayuda: "Qué hiciste tú (no el equipo). Decisiones y trade-offs." },
  { letra: "R", nombre: "Resultado", ayuda: "Cierra con un número o un aprendizaje verificable." },
];

export const PREGUNTAS: Pregunta[] = [
  {
    id: "two-sum-ordenado",
    titulo: "Par con suma objetivo en arreglo ordenado",
    empresa: "Amazon",
    area: "algoritmos",
    dificultad: "facil",
    minutosObjetivo: 12,
    enunciado:
      "Dado un arreglo de enteros ordenado de forma ascendente y un objetivo K, devuelve los índices de los dos números cuya suma sea exactamente K. Se garantiza que existe una única solución.",
    ejemplo: { entrada: "nums = [1, 3, 4, 8, 11], K = 12", salida: "[2, 3]  // 4 + 8" },
    pistas: [
      "Dos punteros: uno al inicio y otro al final.",
      "Si la suma supera K, mueve el puntero derecho.",
      "Complejidad objetivo O(n) tiempo, O(1) espacio.",
    ],
    plantilla: "def par_suma(nums, k):\n    i, j = 0, len(nums) - 1\n    # tu solución aquí\n    return []\n",
  },
  {
    id: "ventana-maxima",
    titulo: "Subarreglo de suma máxima",
    empresa: "Google",
    area: "algoritmos",
    dificultad: "medio",
    minutosObjetivo: 18,
    enunciado:
      "Encuentra el subarreglo contiguo de suma máxima dentro de un arreglo de enteros que puede contener valores negativos. Devuelve la suma.",
    ejemplo: { entrada: "nums = [-2, 1, -3, 4, -1, 2, 1, -5, 4]", salida: "6  // [4,-1,2,1]" },
    pistas: [
      "Piensa en el algoritmo de Kadane.",
      "Mantén el mejor acumulado que termina en la posición i.",
      "Cuidado con el caso de todos negativos.",
    ],
    plantilla: "def suma_maxima(nums):\n    mejor = actual = nums[0]\n    # tu solución aquí\n    return mejor\n",
  },
  {
    id: "lru-cache",
    titulo: "Diseñar una caché LRU",
    empresa: "Meta",
    area: "algoritmos",
    dificultad: "dificil",
    minutosObjetivo: 25,
    enunciado:
      "Implementa una estructura con operaciones get(clave) y put(clave, valor) en O(1) que descarte el elemento menos usado recientemente al superar la capacidad.",
    ejemplo: { entrada: "cap = 2; put(1,1); put(2,2); get(1); put(3,3)", salida: "get(2) -> -1" },
    pistas: [
      "Diccionario + lista doblemente enlazada.",
      "Mueve el nodo al frente en cada acceso.",
      "El nodo cola es siempre el candidato a expulsar.",
    ],
    plantilla:
      "class CacheLRU:\n    def __init__(self, capacidad):\n        self.capacidad = capacidad\n        # tu solución aquí\n\n    def get(self, clave):\n        pass\n\n    def put(self, clave, valor):\n        pass\n",
  },
  {
    id: "bfs-laberinto",
    titulo: "Camino más corto en una cuadrícula",
    empresa: "Microsoft",
    area: "algoritmos",
    dificultad: "medio",
    minutosObjetivo: 20,
    enunciado:
      "Dada una cuadrícula con celdas libres (0) y bloqueadas (1), devuelve la longitud del camino más corto desde la esquina superior izquierda hasta la inferior derecha moviéndote en 4 direcciones.",
    ejemplo: { entrada: "[[0,0,1],[1,0,0],[0,0,0]]", salida: "5" },
    pistas: ["BFS por niveles con cola.", "Marca visitados al encolar, no al desencolar."],
    plantilla:
      "from collections import deque\n\ndef camino_corto(grid):\n    cola = deque([(0, 0, 1)])\n    # tu solución aquí\n    return -1\n",
  },
  {
    id: "acortador-urls",
    titulo: "Diseña un acortador de URLs",
    empresa: "Google",
    area: "sistemas",
    dificultad: "medio",
    minutosObjetivo: 30,
    enunciado:
      "Diseña un servicio que reciba una URL larga y devuelva una corta única, con 100M de lecturas diarias y 1M de escrituras. Define API, esquema de datos, generación de claves, caché y estrategia de escalado.",
    pistas: [
      "Estima primero: QPS de lectura vs escritura.",
      "Codificación base62 sobre un contador distribuido.",
      "Caché de lecturas y réplicas de solo lectura.",
    ],
    plantilla:
      "## API\nPOST /acortar  { url }\nGET  /{codigo}  -> 301\n\n## Datos\n\n## Escalado\n",
  },
  {
    id: "feed-noticias",
    titulo: "Diseña el feed de una red social",
    empresa: "Meta",
    area: "sistemas",
    dificultad: "dificil",
    minutosObjetivo: 35,
    enunciado:
      "Diseña el feed de inicio para 200M de usuarios activos diarios. Discute fan-out en escritura vs lectura, ranking, cuentas con millones de seguidores y consistencia eventual.",
    pistas: [
      "Fan-out en escritura para usuarios normales, en lectura para celebridades.",
      "Separa almacenamiento de timeline del de contenido.",
    ],
    plantilla: "## Requerimientos\n\n## Fan-out\n\n## Ranking\n\n## Cuellos de botella\n",
  },
  {
    id: "rate-limiter",
    titulo: "Diseña un limitador de peticiones",
    empresa: "Amazon",
    area: "sistemas",
    dificultad: "facil",
    minutosObjetivo: 20,
    enunciado:
      "Diseña un rate limiter distribuido de 100 peticiones por minuto por usuario, compartido entre múltiples instancias del servicio.",
    pistas: ["Token bucket vs ventana deslizante.", "Estado compartido en Redis con TTL."],
    plantilla: "## Algoritmo elegido\n\n## Almacenamiento\n\n## Fallos y degradación\n",
  },
];

export const CONDUCTUALES: PreguntaConductual[] = [
  {
    id: "conflicto-equipo",
    pregunta: "Cuéntame sobre un desacuerdo técnico con un compañero y cómo lo resolviste.",
    empresa: "Amazon",
    competencia: "Have Backbone; Disagree and Commit",
    guiaStar: guiaStarBase,
  },
  {
    id: "fallo-produccion",
    pregunta: "Describe una vez en que rompiste algo en producción. ¿Qué hiciste?",
    empresa: "Google",
    competencia: "Ownership",
    guiaStar: guiaStarBase,
  },
  {
    id: "plazo-imposible",
    pregunta: "Háblame de un proyecto con un plazo poco realista y cómo lo manejaste.",
    empresa: "Meta",
    competencia: "Deliver Results",
    guiaStar: guiaStarBase,
  },
  {
    id: "aprender-rapido",
    pregunta: "Cuéntame sobre algo complejo que tuviste que aprender en poco tiempo.",
    empresa: "Anthropic",
    competencia: "Learn and Be Curious",
    guiaStar: guiaStarBase,
  },
];

export const etiquetaDificultad: Record<Dificultad, string> = {
  facil: "Fácil",
  medio: "Medio",
  dificil: "Difícil",
};

export const etiquetaArea: Record<Area, string> = {
  algoritmos: "Algoritmos",
  sistemas: "Sistemas",
  comportamiento: "Comportamiento",
};
