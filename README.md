# Compiler-Anleitung: Von Quellcode zu x86 Assembly

## Was ist ein Compiler?

Ein Compiler übersetzt Quellcode einer Programmiersprache in eine andere Sprache — meistens in eine, die ein Computer direkt ausführen kann. Im Gegensatz zu einem Interpreter, der den Code sofort Zeile für Zeile ausführt, übersetzt der Compiler das gesamte Programm zuerst und führt es danach aus.

Die vollständige Kette sieht so aus:

```
Quellcode → Compiler → Assembly → Assembler → Objektdatei → Linker → Programm
```

- **Assembler (NASM):** Übersetzt die Assembly-Textdatei in echten Maschinencode (Binärdatei).
- **Linker:** Verbindet mehrere Objektdateien und externe Bibliotheken zu einem einzigen ausführbaren Programm.

Unser Compiler übernimmt den ersten Schritt: Quellcode → Assembly.

---

## Input- und Outputsprache

**Input** ist eine selbst erfundene Mini-Sprache. Sie unterstützt:
- Variablenzuweisungen: `a = 1`, `name = 'hello'`
- Arithmetik: `c = a + b`, `m = ((3 + 5) * 7) / 3`
- Funktionen mit Parametern und Rückgabewert
- Funktionsaufrufe: `functionName(3, 5)`
- Ausgabe: `print(d)`

```
def functionName(parameter, parameter2){
    a = 1
    b = 2
    c = a + b
    print(c)
    return c
}
print(functionName(3, 5))
```

**Output** ist x86-64 Assembly im NASM-Format. Jede Zeile ist ein einziger Prozessorbefehl:

```asm
mov rax, 5      ; lade 5 in Register rax
add rax, rbx    ; rax = rax + rbx
```

---

## Die Pipeline

Der Compiler arbeitet in drei aufeinanderfolgenden Phasen. Jede Phase bekommt die Ausgabe der vorherigen als Eingabe:

```
Quellcode (code.txt)
       ↓
   [ Lexer ]        → Token-Liste
       ↓
   [ Parser ]       → Syntaxbaum (AST)
       ↓
 [ Code Generator ] → Assembly (output.asm)
```

---

## Phase 1: Lexer (`lexer.py`)

Der Lexer liest den rohen Quelltext und zerlegt ihn in **Tokens** — die kleinsten sinnvollen Einheiten. Aus `a = 1 + b` werden z.B.:

```
IDENTIFIER  a
OPERATOR    =
NUMBER      1
OPERATOR    +
IDENTIFIER  b
```

**Input:** Textdatei als rohe Zeichenkette  
**Output:** Liste von `Token`-Objekten, jedes mit Typ und Wert

Der Lexer kennt sechs Token-Typen:

| Typ | Beispiele |
|---|---|
| `IDENTIFIER` | `a`, `x`, `functionName` |
| `NUMBER` | `1`, `42` |
| `STRING` | `'hello'` |
| `KEYWORD` | `def`, `print`, `return` |
| `OPERATOR` | `+` `-` `*` `/` `=` |
| `SEPARATOR` | `(` `)` `{` `}` `,` |

Der Lexer liest Zeichen für Zeichen in einer Schleife:
- Leerzeichen → überspringen
- Buchstabe → weiterlesen bis Wortende, dann prüfen ob Keyword oder Identifier
- Ziffer → alle folgenden Ziffern lesen → NUMBER
- `'` oder `"` → bis zum nächsten Anführungszeichen lesen → STRING
- Operator oder Separator → direkt als Token speichern

Ohne den Lexer müsste der Parser direkt auf rohem Text arbeiten. Der Lexer liefert saubere, kategorisierte Bausteine.

---

## Phase 2: Parser (`parser.py`)

Der Parser nimmt die Token-Liste und bringt Struktur hinein. Das Ergebnis ist ein **AST (Abstract Syntax Tree)** — ein Baum, der die hierarchische Struktur des Programms darstellt.

**Input:** Token-Liste  
**Output:** Liste von AST-Knoten

Zum Beispiel wird `a + b * c` zu:

```
BinOp(
  left  = Var(a),
  op    = '+',
  right = BinOp(Var(b), '*', Var(c))
)
```

Die Multiplikation sitzt tiefer im Baum — sie wird zuerst ausgewertet. Das ist Operatorpriorität.

Jede Sprachkonstruktion hat einen eigenen Knotentyp:

| Knoten | Beispiel |
|---|---|
| `Number(value)` | `42` |
| `Var(name)` | `a` |
| `String(value)` | `'hello'` |
| `BinOp(left, op, right)` | `a + b` |
| `Assignment(name, value)` | `a = 1` |
| `Print(value)` | `print(a)` |
| `Return(value)` | `return m` |
| `Function(name, params, body)` | `def f(x){ ... }` |
| `FunctionCall(name, args)` | `f(3, 5)` |

Der Parser verwendet **Recursive Descent Parsing**: Für jede Sprachkonstruktion gibt es eine Methode, die sich bei Bedarf gegenseitig aufrufen. Die Operatorpriorität wird durch drei Ebenen abgebildet:

```
expression()  →  + und -  (niedrigste Priorität)
    ↓
term()        →  * und /
    ↓
factor()      →  Zahlen, Variablen, Klammern  (höchste Priorität)
```

Wenn `expression()` gerufen wird, ruft sie `term()` auf. `term()` ruft `factor()`. So wird `3 + 5 * 7` automatisch korrekt als `3 + (5 * 7)` geparst.

Die zentrale Hilfsmethode ist `eat()` — sie liest das aktuelle Token und rückt den internen Zeiger weiter. Immer wenn der Parser weiß was als nächstes kommen muss (z.B. nach `def` kommt ein Name), ruft er `eat()` auf.

---

## Phase 3: Code Generator (`codegen.py`)

Der Code Generator übersetzt jeden AST-Knoten in Assembly-Befehle. Er verwaltet intern vier Strukturen:

- `code` — Befehle für `_main`
- `functions_code` — Befehle für Funktionen
- `data` — Einträge für die `.data`-Sektion (Strings, globale Variablen)
- `string_vars` — Menge der Variablen, die einen String enthalten (für `gen_Print`)

**Wichtige Konvention:** Nach jeder `generate()`-Methode liegt das Ergebnis immer in `rax`. Alle Methoden halten sich daran.

### Dispatch: `generate()`

```python
def generate(self, node):
    method_name = f"gen_{type(node).__name__}"
    method = getattr(self, method_name, self.no_gen)
    return method(node)
```

Aus dem Knotentyp wird automatisch der Methodenname gebaut. `BinOp` → `gen_BinOp`. Um einen neuen Knotentyp zu unterstützen, reicht eine neue `gen_Xxx`-Methode.

### Zahlen: `gen_Number`
Zahl direkt in `rax` laden:
```asm
mov rax, 42
```

### Variablen: `gen_Var`
Variablen können an drei Orten liegen:
- **Lokale Variable** einer Funktion → `mov rax, [rbp - offset]`
- **Parameter** einer Funktion → `mov rax, [rbp + offset]`
- **Globale Variable** → `mov rax, [rel name]`

### Ausdrücke: `gen_BinOp`
Das Problem: Beide Seiten brauchen `rax`, aber es gibt nur ein `rax`. Die Lösung ist der Stack als temporärer Speicher:

```python
self.generate(node.left)   # linke Seite → rax
self.emit("push rax")      # rax auf Stack sichern
self.generate(node.right)  # rechte Seite → rax
self.emit("pop rbx")       # linke Seite zurückholen → rbx
# jetzt: rbx = links, rax = rechts
```

Danach die Operation:
- `+` → `add rax, rbx`
- `-` → `sub rbx, rax` dann `mov rax, rbx` (links minus rechts)
- `*` → `imul rax, rbx`
- `/` → `xchg rax, rbx` (tauschen), dann `cqo` + `idiv rbx`

Bei Division muss `xchg` die Register tauschen, weil `idiv` immer `rax ÷ rbx` berechnet — nach dem `pop` liegt links aber in `rbx` und rechts in `rax`.

### Strings: `gen_String`
Strings können nicht in ein Register — sie liegen im Datensegment. Der Generator erstellt für jeden String ein eindeutiges Label:

```python
label = f"str{self.string_count}"
self.string_count += 1
self.data.append(f'{label} db "{node.value}", 0')
self.emit(f"lea rax, [rel {label}]")
```

`lea` lädt die **Adresse** des Strings in `rax`, nicht den Wert. `string_count` stellt sicher, dass jedes Label eindeutig ist (`str0`, `str1`, ...).

### Ausgabe: `gen_Print`
`printf` braucht je nach Typ unterschiedliche Argumente. Zahlen brauchen einen Formatstring (`%ld`), Strings zeigen direkt auf die Daten:

```python
is_string = (
    type(node.value).__name__ == "String" or
    (type(node.value).__name__ == "Var" and node.value.name in self.string_vars)
)

if is_string:
    # rax hat bereits die Stringadresse → direkt in rdi (1. Argument)
    self.emit("mov rdi, rax")
else:
    # Zahl → rsi (2. Argument), Formatstring → rdi (1. Argument)
    self.emit("mov rsi, rax")
    self.emit("lea rdi, [rel fmt]")

self.emit("xor rax, rax")
self.emit("and rsp, -16")   # Stack auf 16 Byte ausrichten (ABI-Pflicht)
self.emit("call _printf")
```

Das `and rsp, -16` ist nötig weil die x86-64 ABI verlangt, dass der Stack vor jedem externen Aufruf 16-Byte-ausgerichtet ist. Diese eine Instruktion rundet `rsp` nach unten ab.

### Funktionen: `gen_Function`
Beim Aufruf einer Funktion baut der Generator einen **Stack Frame** auf:

```
┌─────────────┐
│ Parameter 2 │  [rbp + 24]
│ Parameter 1 │  [rbp + 16]
│ Rücksprung  │  [rbp +  8]   ← von call gepusht
│ altes rbp   │  [rbp +  0]   ← von push rbp gepusht
│ Lokale Var1 │  [rbp -  8]
│ Lokale Var2 │  [rbp - 16]
└─────────────┘
```

Ablauf:
1. Einsprungpunkt-Label setzen: `functionName:`
2. `push rbp` / `mov rbp, rsp` — Frame aufbauen
3. Parameter-Offsets berechnen (oberhalb `rbp`)
4. Lokale Variablen zählen, `sub rsp, N` — Platz auf Stack reservieren
5. Jeden Statement im Body generieren
6. Falls kein `return` → `mov rax, 0` + Epilog als Fallback

### Rückgabe: `gen_Return`
```asm
; Rückgabewert bereits in rax
mov rsp, rbp    ; Stack zurücksetzen
pop rbp         ; alten Frame-Pointer wiederherstellen
ret             ; zur Aufrufstelle zurückspringen
```

### Funktionsaufrufe: `gen_FunctionCall`
Argumente werden in **umgekehrter Reihenfolge** gepusht, damit das erste Argument zuletzt gepusht wird und direkt bei `[rbp + 16]` liegt:

```python
for arg in reversed(node.args):
    self.generate(arg)
    self.emit("push rax")

self.emit(f"call {node.name}")
self.emit(f"add rsp, {len(node.args) * 8}")  # Stack bereinigen
```

Nach `ret` liegt der Rückgabewert in `rax` — bereit für die weitere Verarbeitung.

### Zusammenbauen: `get_program()`
Fügt alle Teile zur fertigen Assembly-Datei zusammen:

```
section .data
    fmt db "%ld", 10, 0
    str0 db "hello", 0
    ...globale Variablen...

section .text
    global _main
    extern _printf
    extern _exit

_main:
    ...Hauptcode...
    and rsp, -16
    mov rdi, 0
    call _exit

functionName:
    ...Funktionscode...
```

---

## Einstiegspunkt: `compiler.py`

```python
tokens  = lex(file)         # Phase 1: Quelltext → Tokens
ast     = parser.parse()    # Phase 2: Tokens    → AST
for stmt in ast:
    gen.generate(stmt)      # Phase 3: AST       → Assembly
```

Jede Phase weiß nichts von den anderen — sie kommunizieren nur über ihre Datenstrukturen. Das macht den Compiler modular und erweiterbar.

---

## Zusammenfassung

| Phase | Modul | Input | Output |
|---|---|---|---|
| Lexer | `lexer.py` | Quelltext | Token-Liste |
| Parser | `parser.py` | Token-Liste | AST |
| Code Generator | `codegen.py` | AST | Assembly |
| *(Assembler)* | *NASM* | *Assembly* | *Objektdatei* |
| *(Linker)* | *ld* | *Objektdatei* | *Programm* |

---

## Bonus: Der Interpreter (`interpreter.py`)

Der Interpreter ist kein Bestandteil der Compiler-Pipeline. Er ist als separate Lernkomponente im Repository enthalten um zu zeigen wie der gleiche AST auf eine völlig andere Art ausgewertet werden kann.

Anstatt Assembly zu generieren, läuft der Interpreter direkt über den AST und **führt jeden Knoten sofort aus** — kein Zwischenschritt, kein Output, keine Datei. Das Programm wird in Python selbst ausgeführt.

**Input:** AST (identisch zum Input des Code Generators)  
**Output:** Direktes Ergebnis im Terminal — keine Datei wird erzeugt

```
Quellcode (code.txt)
       ↓
   [ Lexer ]
       ↓
   [ Parser ]
       ↓
      AST
      / \
     /   \
[Interpreter]   [Code Generator]
     ↓                 ↓
Direktes Output    output.asm
```

Der Interpreter verwaltet eine **Umgebung** (`environment`) — ein Dictionary das Variablennamen auf ihre aktuellen Werte abbildet:

```python
environment = {
    "a": 1,
    "b": 2,
    "name": "hello"
}
```

Bei einer Zuweisung wie `a = 1 + 2` wertet er den Ausdruck aus und speichert das Ergebnis direkt in diesem Dictionary. Bei `print(a)` schlägt er `a` im Dictionary nach und gibt den Wert aus. Funktionen bekommen ihre eigene lokale Umgebung die nach dem Aufruf wieder verworfen wird.

Der große Vorteil eines Interpreters ist Einfachheit — kein Stack Frame, keine Register, keine Speicherverwaltung. Der Nachteil ist Geschwindigkeit: Jedes Mal wenn das Programm läuft, muss der AST erneut durchlaufen werden. Ein kompiliertes Programm läuft direkt auf dem Prozessor und ist typischerweise um ein Vielfaches schneller.
