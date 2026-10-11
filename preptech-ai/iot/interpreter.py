"""Simulador IoT propio (costo 0): intérprete de un subconjunto de C/Arduino.

No ejecuta hardware ni código nativo: tokeniza y evalúa el sketch en Python con un
reloj virtual, devolviendo una línea de tiempo de eventos (pines y monitor serie).
Límites de pasos y de tiempo virtual evitan bucles infinitos.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

MAX_STEPS = 200_000
MAX_EVENTS = 2_000

BOARDS = {
    "esp32": {"nombre": "ESP32 DevKit", "adc_max": 4095, "led_builtin": 2,
              "consts": {"A0": 36, "A3": 39, "A6": 34, "A7": 35}},
    "arduino-uno": {"nombre": "Arduino Uno", "adc_max": 1023, "led_builtin": 13,
                    "consts": {"A0": 14, "A1": 15, "A2": 16, "A3": 17, "A4": 18, "A5": 19}},
}
TYPES = {"void", "int", "long", "float", "double", "bool", "boolean", "byte", "char",
         "unsigned", "short", "uint8_t", "uint16_t", "uint32_t", "const", "static"}
INT_TYPES = {"int", "long", "byte", "uint8_t", "uint16_t", "uint32_t", "short", "unsigned"}


class SketchError(Exception):
    def __init__(self, msg: str, line: int | None = None):
        super().__init__(msg)
        self.msg, self.line = msg, line


class _Stop(Exception):
    pass


class _Return(Exception):
    def __init__(self, v=None):
        self.v = v


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


# ---------------------------------------------------------------- tokenizer
_TOKEN = re.compile(r"""
    (?P<ws>\s+)|(?P<num>0[xX][0-9a-fA-F]+|\d+\.\d*|\.\d+|\d+)|(?P<str>"(?:\\.|[^"\\])*")
    |(?P<chr>'(?:\\.|[^'\\])')|(?P<id>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)
    |(?P<op>\+\+|--|\+=|-=|\*=|/=|%=|==|!=|<=|>=|&&|\|\||<<|>>|[-+*/%<>=!&|^~(){}\[\];,?:])
""", re.VERBOSE)


@dataclass
class Tok:
    k: str
    v: str
    line: int


def tokenize(src: str) -> list[Tok]:
    src = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    defines: dict[str, str] = {}
    lines = []
    for ln in src.split("\n"):
        s = ln.strip()
        if s.startswith("#define"):
            parts = s.split(None, 2)
            if len(parts) == 3:
                defines[parts[1]] = parts[2].strip()
            lines.append("")
        elif s.startswith("#"):
            lines.append("")
        else:
            lines.append(ln)
    out, line = [], 1
    for ln in lines:
        pos = 0
        while pos < len(ln):
            m = _TOKEN.match(ln, pos)
            if not m:
                raise SketchError(f"Carácter no reconocido: {ln[pos]!r}", line)
            pos = m.end()
            k = m.lastgroup
            if k == "ws":
                continue
            v = m.group(k)
            if k == "id" and v in defines:
                for t in tokenize(defines[v]):
                    out.append(Tok(t.k, t.v, line))
                continue
            out.append(Tok(k, v, line))
        line += 1
    return out


# ------------------------------------------------------------------- parser
class Parser:
    def __init__(self, toks: list[Tok]):
        self.t, self.i = toks, 0

    def peek(self, o=0):
        return self.t[self.i + o] if self.i + o < len(self.t) else Tok("eof", "", self.t[-1].line if self.t else 1)

    def next(self):
        tok = self.peek()
        self.i += 1
        return tok

    def accept(self, v):
        if self.peek().v == v and self.peek().k in ("op", "id"):
            self.i += 1
            return True
        return False

    def expect(self, v):
        tok = self.next()
        if tok.v != v:
            raise SketchError(f"Se esperaba '{v}' y se encontró '{tok.v or 'fin del archivo'}'", tok.line)
        return tok

    # --- programa
    def program(self):
        globs, funcs = [], {}
        while self.peek().k != "eof":
            start = self.i
            ty = self.type_()
            if not ty:
                raise SketchError(f"Declaración inesperada: '{self.peek().v}'", self.peek().line)
            name = self.next()
            if name.k != "id":
                raise SketchError("Se esperaba un nombre", name.line)
            if self.peek().v == "(":
                self.next()
                params = []
                while self.peek().v != ")":
                    pty = self.type_()
                    pn = self.next()
                    if not pty or pn.k != "id":
                        raise SketchError("Parámetro inválido", pn.line)
                    params.append(pn.v)
                    if not self.accept(","):
                        break
                self.expect(")")
                funcs[name.v] = (params, self.block())
            else:
                self.i = start
                globs.append(self.decl())
        return globs, funcs

    def type_(self):
        words = []
        while self.peek().k == "id" and self.peek().v in TYPES:
            words.append(self.next().v)
        return words

    def decl(self):
        line = self.peek().line
        ty = self.type_()
        items = []
        while True:
            name = self.next()
            if name.k != "id":
                raise SketchError("Se esperaba un nombre de variable", name.line)
            if self.peek().v == "[":
                raise SketchError("Los arreglos aún no están soportados en el simulador", name.line)
            init = self.expr() if self.accept("=") else None
            items.append((name.v, init))
            if not self.accept(","):
                break
        self.expect(";")
        return ("decl", ty, items, line)

    def block(self):
        self.expect("{")
        out = []
        while self.peek().v != "}":
            if self.peek().k == "eof":
                raise SketchError("Falta cerrar una llave '}'", self.peek().line)
            out.append(self.stmt())
        self.expect("}")
        return ("block", out)

    def stmt(self):
        tok = self.peek()
        if tok.v == "{":
            return self.block()
        if tok.k == "id" and tok.v in TYPES:
            return self.decl()
        if tok.k == "id" and tok.v == "if":
            self.next()
            self.expect("(")
            c = self.expr()
            self.expect(")")
            a = self.stmt()
            b = self.stmt() if self.accept("else") else None
            return ("if", c, a, b)
        if tok.k == "id" and tok.v == "while":
            self.next()
            self.expect("(")
            c = self.expr()
            self.expect(")")
            return ("while", c, self.stmt())
        if tok.k == "id" and tok.v == "for":
            self.next()
            self.expect("(")
            if self.peek().v == ";":
                init = None
                self.next()
            elif self.peek().v in TYPES:
                init = self.decl()  # consume el ';'
            else:
                init = self.simple()
                self.expect(";")
            cond = None if self.peek().v == ";" else self.expr()
            self.expect(";")
            step = None if self.peek().v == ")" else self.expr()
            self.expect(")")
            return ("for", init, cond, step, self.stmt())
        if tok.k == "id" and tok.v == "return":
            self.next()
            v = None if self.peek().v == ";" else self.expr()
            self.expect(";")
            return ("return", v)
        if tok.k == "id" and tok.v in ("break", "continue"):
            self.next()
            self.expect(";")
            return (tok.v,)
        if tok.v == ";":
            self.next()
            return ("block", [])
        s = self.simple()
        self.expect(";")
        return s

    def simple(self):
        line = self.peek().line
        return ("expr", self.expr(), line)

    # --- expresiones
    def expr(self):
        left = self.ternary()
        tok = self.peek()
        if tok.k == "op" and tok.v in ("=", "+=", "-=", "*=", "/=", "%="):
            if left[0] != "var":
                raise SketchError("Solo se puede asignar a una variable", tok.line)
            self.next()
            return ("assign", left[1], tok.v, self.expr(), tok.line)
        return left

    def ternary(self):
        c = self.binary(0)
        if self.accept("?"):
            a = self.expr()
            self.expect(":")
            return ("tern", c, a, self.expr())
        return c

    LEVELS = [["||"], ["&&"], ["|"], ["^"], ["&"], ["==", "!="], ["<", ">", "<=", ">="],
              ["<<", ">>"], ["+", "-"], ["*", "/", "%"]]

    def binary(self, lvl):
        if lvl == len(self.LEVELS):
            return self.unary()
        left = self.binary(lvl + 1)
        while self.peek().k == "op" and self.peek().v in self.LEVELS[lvl]:
            op = self.next()
            left = ("bin", op.v, left, self.binary(lvl + 1), op.line)
        return left

    def unary(self):
        tok = self.peek()
        if tok.k == "op" and tok.v in ("!", "-", "+", "~"):
            self.next()
            return ("un", tok.v, self.unary())
        if tok.k == "op" and tok.v in ("++", "--"):
            self.next()
            v = self.unary()
            if v[0] != "var":
                raise SketchError("++/-- solo aplica a variables", tok.line)
            return ("assign", v[1], "+=" if tok.v == "++" else "-=", ("num", 1), tok.line)
        return self.postfix()

    def postfix(self):
        e = self.primary()
        tok = self.peek()
        if tok.k == "op" and tok.v in ("++", "--") and e[0] == "var":
            self.next()
            return ("post", e[1], 1 if tok.v == "++" else -1, tok.line)
        return e

    def primary(self):
        tok = self.next()
        if tok.k == "num":
            v = tok.v
            return ("num", int(v, 16) if v.lower().startswith("0x") else float(v) if "." in v else int(v))
        if tok.k == "str":
            return ("str", tok.v[1:-1].replace("\\n", "\n").replace('\\"', '"'))
        if tok.k == "chr":
            return ("str", tok.v[1:-1])
        if tok.k == "id":
            if self.peek().v == "(":
                self.next()
                args = []
                while self.peek().v != ")":
                    args.append(self.expr())
                    if not self.accept(","):
                        break
                self.expect(")")
                return ("call", tok.v, args, tok.line)
            return ("var", tok.v, tok.line)
        if tok.v == "(":
            e = self.expr()
            self.expect(")")
            return e
        raise SketchError(f"Expresión inesperada: '{tok.v or 'fin del archivo'}'", tok.line)


# ------------------------------------------------------------------ runtime
@dataclass
class Result:
    ok: bool = True
    error: str | None = None
    error_line: int | None = None
    events: list[dict] = field(default_factory=list)
    serial: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    pin_modes: dict[int, str] = field(default_factory=dict)
    duration_ms: int = 0
    loops: int = 0


def _c_div(a, b, line):
    if b == 0:
        raise SketchError("División entre cero", line)
    if isinstance(a, int) and isinstance(b, int):
        q = abs(a) // abs(b)
        return q if (a >= 0) == (b >= 0) else -q
    return a / b


class Machine:
    def __init__(self, board: str, inputs: dict, duration_ms: int):
        self.b = BOARDS[board]
        self.duration = duration_ms
        self.t = 0.0
        self.steps = 0
        self.res = Result()
        self.globals: dict = {"HIGH": 1, "LOW": 0, "INPUT": 0, "OUTPUT": 1, "INPUT_PULLUP": 2,
                              "true": 1, "false": 0, "LED_BUILTIN": self.b["led_builtin"], "PI": 3.14159265,
                              **self.b["consts"]}
        self.inputs = {int(k): v for k, v in (inputs or {}).items()}
        self.funcs: dict = {}
        self.scopes: list[dict] = []
        self.pin_val: dict[int, int] = {}
        self.line = 0
        self.serial_buf = ""

    def _input(self, pin: int) -> float:
        """Entrada física: número fijo o lista [[t_ms, valor], ...] (escalones en el tiempo)."""
        v = self.inputs.get(pin, 0)
        if isinstance(v, list):
            cur = 0
            for t, val in v:
                if self.t >= t:
                    cur = val
            return cur
        return v

    def tick(self):
        self.steps += 1
        if self.steps > MAX_STEPS:
            raise SketchError("El programa ejecutó demasiadas instrucciones sin pausa. ¿Falta un delay() en el bucle?", self.line)

    def emit(self, channel, **kw):
        if len(self.res.events) + len(self.res.serial) > MAX_EVENTS:
            raise _Stop()
        (self.res.events if channel == "pin" else self.res.serial).append({"t": int(self.t), **kw})

    def delay(self, ms):
        self.t += max(0, ms)
        if self.t >= self.duration:
            raise _Stop()

    def lookup(self, name, line):
        for sc in reversed(self.scopes):
            if name in sc:
                return sc
        if name in self.globals:
            return self.globals
        raise SketchError(f"Variable no declarada: '{name}'", line)

    def call(self, name, args, line):
        self.line = line or self.line
        a = [self.ev(x) for x in args]
        pm = self.res.pin_modes
        if name in self.funcs:
            params, body = self.funcs[name]
            if len(a) != len(params):
                raise SketchError(f"'{name}' espera {len(params)} argumento(s)", line)
            self.scopes.append(dict(zip(params, a)))
            try:
                self.exec(body)
            except _Return as r:
                return r.v
            finally:
                self.scopes.pop()
            return 0
        n = len(a)

        def need(k):
            if n != k:
                raise SketchError(f"'{name}' espera {k} argumento(s)", line)
        if name == "pinMode":
            need(2)
            pin = int(a[0])
            pm[pin] = {0: "INPUT", 1: "OUTPUT", 2: "INPUT_PULLUP"}.get(int(a[1]), "INPUT")
            self.emit("pin", pin=pin, kind="mode", value=pm[pin])
        elif name == "digitalWrite":
            need(2)
            pin, v = int(a[0]), 1 if a[1] else 0
            if pm.get(pin) != "OUTPUT":
                self.res.warnings.append(f"Línea {line}: digitalWrite en el pin {pin} sin pinMode({pin}, OUTPUT).")
                pm[pin] = "OUTPUT"
            if self.pin_val.get(pin) != v:
                self.emit("pin", pin=pin, kind="digital", value=v)
            self.pin_val[pin] = v
        elif name in ("analogWrite", "ledcWrite"):
            need(2)
            pin, v = int(a[0]), max(0, min(255, int(a[1])))
            self.emit("pin", pin=pin, kind="pwm", value=v)
            self.pin_val[pin] = v
        elif name == "digitalRead":
            need(1)
            pin = int(a[0])
            if pin not in pm:
                self.res.warnings.append(f"Línea {line}: digitalRead del pin {pin} sin pinMode.")
            pressed = 1 if self._input(pin) else 0
            return (1 - pressed) if pm.get(pin) == "INPUT_PULLUP" else pressed
        elif name == "analogRead":
            need(1)
            pct = max(0, min(100, self._input(int(a[0]))))
            return int(round(pct / 100 * self.b["adc_max"]))
        elif name == "delay":
            need(1)
            self.delay(a[0])
        elif name == "delayMicroseconds":
            need(1)
            self.delay(a[0] / 1000)
        elif name == "millis":
            return int(self.t)
        elif name == "map":
            need(5)
            x, i0, i1, o0, o1 = a
            return int((x - i0) * (o1 - o0) / (i1 - i0) + o0) if i1 != i0 else o0
        elif name == "constrain":
            need(3)
            return max(a[1], min(a[2], a[0]))
        elif name in ("abs", "min", "max"):
            return {"abs": abs, "min": min, "max": max}[name](*a)
        elif name == "Serial.begin":
            pass
        elif name in ("Serial.print", "Serial.println"):
            txt = "" if not a else (a[0] if isinstance(a[0], str) else
                                    (f"{a[0]:.2f}" if isinstance(a[0], float) else str(a[0])))
            self.serial_buf += txt
            if name.endswith("ln"):
                self.emit("serial", text=self.serial_buf)
                self.serial_buf = ""
        else:
            raise SketchError(f"Función desconocida: '{name}'", line)
        return 0

    def ev(self, e):
        self.tick()
        k = e[0]
        if k in ("num", "str"):
            return e[1]
        if k == "var":
            return self.lookup(e[1], e[2])[e[1]]
        if k == "call":
            return self.call(e[1], e[2], e[3])
        if k == "un":
            v = self.ev(e[2])
            return {"!": int(not v), "-": -v, "+": v, "~": ~int(v)}[e[1]]
        if k == "post":
            sc = self.lookup(e[1], e[3])
            old = sc[e[1]]
            sc[e[1]] = old + e[2]
            return old
        if k == "tern":
            return self.ev(e[2]) if self.ev(e[1]) else self.ev(e[3])
        if k == "assign":
            sc = self.lookup(e[1], e[4])
            v = self.ev(e[3])
            if e[2] != "=":
                v = self.binop(e[2][0], sc[e[1]], v, e[4])
            sc[e[1]] = v
            return v
        if k == "bin":
            op = e[1]
            if op == "&&":
                return int(bool(self.ev(e[2])) and bool(self.ev(e[3])))
            if op == "||":
                return int(bool(self.ev(e[2])) or bool(self.ev(e[3])))
            return self.binop(op, self.ev(e[2]), self.ev(e[3]), e[4])
        raise SketchError("Expresión no soportada", self.line)

    def binop(self, op, a, b, line):
        if isinstance(a, str) or isinstance(b, str):
            raise SketchError("Los textos solo se pueden usar dentro de Serial.print/println", line)
        if op == "/":
            return _c_div(a, b, line)
        if op == "%":
            if int(b) == 0:
                raise SketchError("Módulo entre cero", line)
            r = abs(int(a)) % abs(int(b))
            return r if a >= 0 else -r
        ops = {"+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b, "<": lambda: int(a < b),
               ">": lambda: int(a > b), "<=": lambda: int(a <= b), ">=": lambda: int(a >= b),
               "==": lambda: int(a == b), "!=": lambda: int(a != b), "&": lambda: int(a) & int(b),
               "|": lambda: int(a) | int(b), "^": lambda: int(a) ^ int(b),
               "<<": lambda: int(a) << int(b), ">>": lambda: int(a) >> int(b)}
        return ops[op]()

    def exec(self, s):
        self.tick()
        k = s[0]
        if k == "block":
            self.scopes.append({})
            try:
                for x in s[1]:
                    self.exec(x)
            finally:
                self.scopes.pop()
        elif k == "decl":
            self.line = s[3]
            for name, init in s[2]:
                v = self.ev(init) if init is not None else 0
                if isinstance(v, float) and any(t in INT_TYPES for t in s[1]):
                    v = int(v)
                (self.scopes[-1] if self.scopes else self.globals)[name] = v
        elif k == "expr":
            self.line = s[2]
            self.ev(s[1])
        elif k == "if":
            if self.ev(s[1]):
                self.exec(s[2])
            elif s[3] is not None:
                self.exec(s[3])
        elif k == "while":
            while self.ev(s[1]):
                try:
                    self.exec(s[2])
                except _Break:
                    break
                except _Continue:
                    continue
        elif k == "for":
            self.scopes.append({})
            try:
                if s[1] is not None:
                    self.exec(s[1])
                while s[2] is None or self.ev(s[2]):
                    try:
                        self.exec(s[4])
                    except _Break:
                        break
                    except _Continue:
                        pass
                    if s[3] is not None:
                        self.ev(s[3])
            finally:
                self.scopes.pop()
        elif k == "return":
            raise _Return(self.ev(s[1]) if s[1] is not None else None)
        elif k == "break":
            raise _Break()
        elif k == "continue":
            raise _Continue()


def simulate(code: str, board: str = "esp32", inputs: dict | None = None, duration_ms: int = 5000) -> Result:
    if board not in BOARDS:
        raise ValueError(f"Placa desconocida: {board}")
    duration_ms = max(500, min(int(duration_ms), 30_000))
    m = Machine(board, inputs or {}, duration_ms)
    try:
        globs, funcs = Parser(tokenize(code)).program()
        if "setup" not in funcs or "loop" not in funcs:
            raise SketchError("El sketch necesita las funciones setup() y loop().")
        m.funcs = funcs
        for g in globs:
            m.exec(g)
        try:
            m.call("setup", [], 0)
            while True:
                before = m.t
                m.call("loop", [], 0)
                m.res.loops += 1
                if m.t == before and m.res.loops > 1000:
                    raise SketchError("El loop() no usa delay(): se repite sin avanzar el tiempo.", m.line)
        except _Stop:
            pass
    except SketchError as e:
        m.res.ok, m.res.error, m.res.error_line = False, e.msg, e.line
    except (RecursionError, _Return, _Break, _Continue):
        m.res.ok, m.res.error = False, "Estructura de control inválida (return/break fuera de lugar o recursión)."
    m.res.duration_ms = min(int(m.t), duration_ms)
    return m.res
