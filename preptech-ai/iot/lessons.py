"""Lecciones del módulo IoT: contenido, dispositivos simulados y verificación automática.

Cada lección define un `scenario` (entradas fijas del "mundo físico") con el que se
valida el sketch del estudiante, independiente de lo que él pruebe a mano.
"""
from __future__ import annotations

from .interpreter import Result


def pin_at(res: Result, pin: int, t: int) -> int:
    """Valor digital del pin en el instante t (ms) según la línea de tiempo."""
    v = 0
    for e in res.events:
        if e["pin"] == pin and e["kind"] == "digital" and e["t"] <= t:
            v = e["value"]
    return v


def toggles(res: Result, pin: int) -> int:
    return sum(1 for e in res.events if e["pin"] == pin and e["kind"] == "digital")


def _blink_checks(r: Result) -> list[tuple[str, bool]]:
    return [
        ("Configuraste el pin 2 como OUTPUT", r.pin_modes.get(2) == "OUTPUT"),
        ("El LED cambia de estado al menos 4 veces en 5 s", toggles(r, 2) >= 4),
        ("El LED enciende y apaga (no se queda fijo)", {0, 1} <= {pin_at(r, 2, t) for t in range(0, 5000, 250)}),
    ]


def _button_checks(r: Result) -> list[tuple[str, bool]]:
    return [
        ("Configuraste el pin 4 como entrada (INPUT_PULLUP)", r.pin_modes.get(4) == "INPUT_PULLUP"),
        ("Configuraste el pin 2 como OUTPUT", r.pin_modes.get(2) == "OUTPUT"),
        ("Con el botón suelto el LED está apagado", pin_at(r, 2, 500) == 0 and pin_at(r, 2, 3500) == 0),
        ("Mientras el botón está presionado el LED está encendido", pin_at(r, 2, 1500) == 1 and pin_at(r, 2, 2200) == 1),
    ]


def _sensor_checks(r: Result) -> list[tuple[str, bool]]:
    nums = [s["text"] for s in r.serial]
    return [
        ("Imprimes lecturas por el monitor serie", len(nums) >= 3),
        ("Con luz alta (sensor bajo) el LED permanece apagado", pin_at(r, 2, 1000) == 0),
        ("Con poca luz (sensor alto) el LED se enciende", pin_at(r, 2, 4000) == 1),
    ]


LESSONS = [
    {
        "id": "blink", "titulo": "1. Hola mundo: parpadear un LED", "nivel": "Básico", "board": "esp32",
        "objetivo": "Configurar un pin como salida y alternar su estado con delay().",
        "teoria": [
            "setup() corre una vez; loop() se repite para siempre.",
            "pinMode(pin, OUTPUT) prepara el pin; digitalWrite(pin, HIGH/LOW) enciende o apaga.",
            "delay(ms) pausa el programa. Sin delay el parpadeo sería invisible.",
        ],
        "devices": [{"type": "led", "pin": 2, "label": "LED integrado (GPIO 2)", "color": "#a3e635"}],
        "controls": [],
        "starter": ("// Hace parpadear el LED cada segundo\n"
                    "const int LED = 2;\n\n"
                    "void setup() {\n  Serial.begin(115200);\n  // TODO: configura el pin del LED como salida\n}\n\n"
                    "void loop() {\n  // TODO: enciende, espera 500 ms, apaga, espera 500 ms\n}\n"),
        "solution": ("const int LED = 2;\n\nvoid setup() {\n  Serial.begin(115200);\n  pinMode(LED, OUTPUT);\n}\n\n"
                     "void loop() {\n  digitalWrite(LED, HIGH);\n  delay(500);\n  digitalWrite(LED, LOW);\n  delay(500);\n}\n"),
        "scenario": {}, "checks": _blink_checks,
    },
    {
        "id": "boton", "titulo": "2. Entrada digital: botón y LED", "nivel": "Básico", "board": "esp32",
        "objetivo": "Leer un pulsador con INPUT_PULLUP y encender el LED solo mientras se presiona.",
        "teoria": [
            "INPUT_PULLUP activa una resistencia interna: el pin lee HIGH en reposo y LOW al presionar.",
            "digitalRead(pin) devuelve HIGH o LOW. Usa if/else para decidir qué hacer.",
            "Un pulsador entre el pin 4 y GND no necesita resistencia externa con pull-up.",
        ],
        "devices": [{"type": "led", "pin": 2, "label": "LED (GPIO 2)", "color": "#a3e635"},
                    {"type": "button", "pin": 4, "label": "Pulsador (GPIO 4 → GND)"}],
        "controls": [{"type": "button", "pin": 4, "label": "Mantener presionado el botón"}],
        "starter": ("const int LED = 2;\nconst int BOTON = 4;\n\n"
                    "void setup() {\n  pinMode(LED, OUTPUT);\n  // TODO: configura BOTON con INPUT_PULLUP\n}\n\n"
                    "void loop() {\n  // TODO: lee el botón; si está presionado (LOW) enciende el LED, si no apágalo\n  delay(10);\n}\n"),
        "solution": ("const int LED = 2;\nconst int BOTON = 4;\n\nvoid setup() {\n  pinMode(LED, OUTPUT);\n  pinMode(BOTON, INPUT_PULLUP);\n}\n\n"
                     "void loop() {\n  if (digitalRead(BOTON) == LOW) {\n    digitalWrite(LED, HIGH);\n  } else {\n    digitalWrite(LED, LOW);\n  }\n  delay(10);\n}\n"),
        "scenario": {"4": [[1000, 1], [2500, 0]]}, "checks": _button_checks,
    },
    {
        "id": "sensor", "titulo": "3. Sensor analógico + monitor serie", "nivel": "Intermedio", "board": "esp32",
        "objetivo": "Leer un sensor de luz (LDR) con analogRead, mostrar el valor y encender el LED cuando hay poca luz.",
        "teoria": [
            "analogRead(pin) devuelve 0–4095 en el ESP32 (ADC de 12 bits) y 0–1023 en Arduino Uno.",
            "Serial.println(valor) escribe en el monitor serie para depurar.",
            "Un umbral (if valor > 2000) convierte una lectura continua en una decisión.",
        ],
        "devices": [{"type": "led", "pin": 2, "label": "LED (GPIO 2)", "color": "#fbbf24"},
                    {"type": "sensor", "pin": 34, "label": "Sensor de oscuridad (GPIO 34)"}],
        "controls": [{"type": "slider", "pin": 34, "label": "Oscuridad ambiental (%)", "min": 0, "max": 100, "value": 20}],
        "starter": ("const int LED = 2;\nconst int SENSOR = 34;\nconst int UMBRAL = 2000;\n\n"
                    "void setup() {\n  Serial.begin(115200);\n  pinMode(LED, OUTPUT);\n}\n\n"
                    "void loop() {\n  int valor = analogRead(SENSOR);\n  // TODO: imprime el valor y enciende el LED si valor > UMBRAL\n  delay(500);\n}\n"),
        "solution": ("const int LED = 2;\nconst int SENSOR = 34;\nconst int UMBRAL = 2000;\n\nvoid setup() {\n  Serial.begin(115200);\n  pinMode(LED, OUTPUT);\n}\n\n"
                     "void loop() {\n  int valor = analogRead(SENSOR);\n  Serial.println(valor);\n  digitalWrite(LED, valor > UMBRAL ? HIGH : LOW);\n  delay(500);\n}\n"),
        "scenario": {"34": [[0, 20], [2500, 80]]}, "checks": _sensor_checks,
    },
]
BY_ID = {l["id"]: l for l in LESSONS}


def public(lesson: dict) -> dict:
    """Versión enviable al cliente (sin la solución ni funciones)."""
    return {k: v for k, v in lesson.items() if k not in ("checks", "solution", "scenario")}


def evaluate(lesson_id: str, res: Result) -> list[dict]:
    return [{"label": label, "ok": bool(ok)} for label, ok in BY_ID[lesson_id]["checks"](res)]
