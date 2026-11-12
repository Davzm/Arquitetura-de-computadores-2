# entregavel.py
"""
Entregável: tradutor/executor de instruções IJVM (ILOAD x, DUP, BIPUSH b) na
Mic-1 modificada (etapa3/mic1.py).

Uso:
    python3 etapa3/entregavel.py [instruções.txt] [registradores.txt] [dados.txt] [log.txt]

Sem argumentos, usa `instruções.txt`, `registradores_etapa3_tarefa1.txt` e
`dados_etapa3_tarefa1.txt` desta pasta e grava `log_entregavel.txt`. A memória
é regravada na cópia `<dados>_execucao.txt`; o arquivo original não muda.

Formato de instruções.txt (uma por linha, linhas vazias ignoradas,
maiúsculas/minúsculas indiferentes):
    ILOAD x     x decimal >= 0
    DUP
    BIPUSH b    b = 8 bits em binário (ex.: 00110011)
"""
import os
import re
import sys

from mic1 import STARS, Mic1, run_and_log

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEP = "=" * 60
SUB = "-" * 60

# Microinstruções de 23 bits: ULA(8) | C(9) | MEM(2) | B(4)
MICRO = {
    "H = LV":              "00110100" "100000000" "00" "0101",
    "H = H+1":             "00111001" "100000000" "00" "0000",
    # O exemplo (6) do PDF codifica "MAR = H; rd" com C = 100000000, o que
    # habilitaria H, e não MAR. Isso é um erro do PDF: o correto é
    # C = 000000001 (bit 0 = MAR), usado aqui.
    "MAR = H; rd":         "00111000" "000000001" "01" "0000",
    "MAR = SP = SP+1; wr": "00110101" "000001001" "10" "0100",
    "MAR = SP = SP+1":     "00110101" "000001001" "00" "0100",
    "TOS = MDR":           "00110100" "001000000" "00" "0000",
    "MDR = TOS; wr":       "00110100" "000000010" "10" "0111",
    "MDR = TOS = H; wr":   "00111000" "001000010" "10" "0000",
}


def fetch_micro(byte: str) -> str:
    """fetch: os 8 primeiros bits são o byte de dado; MEM = 11 (WRITE e READ)."""
    return byte + "000000000" + "11" + "0000"


def translate(op: str, arg):
    """Retorna a lista de (mnemônico, microinstrução de 23 bits)."""
    if op == "ILOAD":
        seq = [("H = LV", MICRO["H = LV"])]
        seq += [("H = H+1", MICRO["H = H+1"])] * arg
        seq += [(m, MICRO[m]) for m in ("MAR = H; rd", "MAR = SP = SP+1; wr", "TOS = MDR")]
        return seq
    if op == "DUP":
        return [(m, MICRO[m]) for m in ("MAR = SP = SP+1", "MDR = TOS; wr")]
    if op == "BIPUSH":
        return [
            ("MAR = SP = SP+1", MICRO["MAR = SP = SP+1"]),
            ("fetch", fetch_micro(arg)),
            ("MDR = TOS = H; wr", MICRO["MDR = TOS = H; wr"]),
        ]
    raise ValueError(op)


def parse_line(line: str):
    """Valida uma linha e devolve (op, arg, texto normalizado). Lança ValueError."""
    parts = line.split()
    op = parts[0].upper()
    args = parts[1:]
    if op == "DUP":
        if args:
            raise ValueError("DUP não recebe argumento")
        return op, None, "DUP"
    if op == "ILOAD":
        if len(args) != 1 or not re.fullmatch(r"[0-9]+", args[0]):
            raise ValueError("ILOAD exige exatamente um argumento decimal >= 0 (ex.: ILOAD 1)")
        x = int(args[0])
        return op, x, f"ILOAD {x}"
    if op == "BIPUSH":
        if len(args) != 1 or not re.fullmatch(r"[01]{8}", args[0]):
            raise ValueError("BIPUSH exige exatamente um byte de 8 bits em binário "
                             "(ex.: BIPUSH 00110011)")
        return op, args[0], f"BIPUSH {args[0]}"
    raise ValueError(f"instrução desconhecida {parts[0]!r} (aceitas: ILOAD, DUP, BIPUSH)")


def parse_program(path: str):
    """Lê e valida todo o arquivo antes de executar qualquer coisa."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo de instruções '{path}' não encontrado.")
    program, errors = [], []
    with open(path, "r", encoding="utf-8") as f:
        for num, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            try:
                program.append(parse_line(line))
            except ValueError as exc:
                errors.append(f"{path}:{num}: {exc}: {line!r}")
    if errors:
        raise ValueError("Programa rejeitado:\n  " + "\n  ".join(errors))
    return program


def run_program(instr_file=None, reg_file=None, data_file=None, log_file=None,
                work_mem_file=None, echo=True):
    instr_file = instr_file or os.path.join(BASE_DIR, "instruções.txt")
    reg_file = reg_file or os.path.join(BASE_DIR, "registradores_etapa3_tarefa1.txt")
    data_file = data_file or os.path.join(BASE_DIR, "dados_etapa3_tarefa1.txt")
    log_file = log_file or os.path.join(BASE_DIR, "log_entregavel.txt")
    if work_mem_file is None:
        stem = os.path.splitext(os.path.basename(data_file))[0]
        work_mem_file = os.path.join(BASE_DIR, stem + "_execucao.txt")

    program = parse_program(instr_file)

    machine = Mic1()
    machine.load_initial_registers(reg_file)
    machine.load_memory(data_file, work_mem_file)

    with open(log_file, "w", encoding="utf-8") as logfile:
        def emit(text):
            if echo:
                print(text, end="")
            logfile.write(text)

        emit(f"{SEP}\nInitial memory state\n{STARS}\n{machine.format_memory()}")
        emit(f"{STARS}\nInitial register state\n{STARS}\n{machine.format_registers()}")
        emit(f"{SEP}\nStart of Program\n{SEP}\n")

        for i, (op, arg, text) in enumerate(program, 1):
            emit(f"Instruction {i}: {text}\n")
            for j, (mnemonic, micro) in enumerate(translate(op, arg), 1):
                emit(f"{SUB}\nMicroinstruction {i}.{j}: {mnemonic}\n")
                run_and_log(machine, micro, emit)
            emit(f"{SUB}\n> Memory after instruction {i} ({text})\n{STARS}\n"
                 f"{machine.format_memory()}{SEP}\n")

        emit("No more lines, EOP.\n")
    return machine


if __name__ == "__main__":
    try:
        run_program(*sys.argv[1:5])
    except (ValueError, FileNotFoundError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        sys.exit(1)
