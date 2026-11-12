# etapa2_tarefa1.py
"""
Etapa 2 - Tarefa 1: ULA de 8 sinais de controle com deslocador e flags N/Z.

Uso:
    python3 etapa2/tarefa1.py [programa.txt] [log.txt]

Sem argumentos, lê `programa_etapa2_tarefa1.txt` e grava `log_etapa2_tarefa1.txt`
na mesma pasta deste arquivo.
"""
import os
import sys

# Entradas fixas da ULA (configuráveis). Padrão = teste oficial.
A = 0x00000001
B = 0x80000000

MASK32 = 0xFFFFFFFF
SEP = "=" * 60
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class InvalidControlSignals(Exception):
    """SLL8 e SRA1 ativos ao mesmo tempo (proibido pelo PDF)."""


def ula_8bit_shifter(a_val: int, b_val: int, ir_str: str):
    """
    ULA de 8 bits com Deslocador e Flags N/Z.
    IR (8 bits): [SLL8, SRA1, F0, F1, ENA, ENB, INVA, INC]

    Retorna (a_prime, s, s_d, co, n, z), onde s é a saída da ULA antes do
    deslocador e s_d é a saída deslocada.
    """
    sll8 = int(ir_str[0])
    sra1 = int(ir_str[1])
    f0   = int(ir_str[2])
    f1   = int(ir_str[3])
    ena  = int(ir_str[4])
    enb  = int(ir_str[5])
    inva = int(ir_str[6])
    inc  = int(ir_str[7])

    if sll8 and sra1:
        raise InvalidControlSignals()

    # 1. Habilitação das entradas
    a_prime = (a_val & MASK32) if ena == 1 else 0
    b_prime = (b_val & MASK32) if enb == 1 else 0

    # 2. Inversão de A
    a_op = (~a_prime & MASK32) if inva == 1 else a_prime

    # 3. Operação Principal da ULA
    op = (f0 << 1) | f1
    co = 0

    if op == 0:      # 00: AND
        s = a_op & b_prime
    elif op == 1:    # 01: OR
        s = a_op | b_prime
    elif op == 2:    # 10: NOT B
        s = (~b_prime) & MASK32
    else:            # 11: Addition
        res = a_op + b_prime + inc
        s = res & MASK32
        co = 1 if res > MASK32 else 0

    # 4. Deslocador (Shifter) - atua depois da ULA
    if sll8 == 1:
        s_d = (s << 8) & MASK32
    elif sra1 == 1:
        # Deslocamento aritmético à direita (preserva o bit de sinal de 32 bits)
        s_signed = s if s < 0x80000000 else s - 0x100000000
        s_d = (s_signed >> 1) & MASK32
    else:
        s_d = s

    # 5. Flags N e Z (calculadas sobre a saída deslocada Sd)
    z = 1 if s_d == 0 else 0
    n = 1 if (s_d & 0x80000000) != 0 else 0

    return a_prime, s, s_d, co, n, z


def executar_tarefa1(input_file=None, log_file=None, a_fixed=A, b_fixed=B):
    input_file = input_file or os.path.join(BASE_DIR, "programa_etapa2_tarefa1.txt")
    log_file = log_file or os.path.join(BASE_DIR, "log_etapa2_tarefa1.txt")
    pc = 1

    if not os.path.exists(input_file):
        print(f"Erro: Arquivo '{input_file}' não encontrado.")
        return

    def emit(text, logfile):
        print(text, end="")
        logfile.write(text)

    with open(input_file, "r") as infile, open(log_file, "w") as logfile:
        emit(f"b = {b_fixed:032b}\na = {a_fixed:032b}\n\nStart of Program\n{SEP}\n", logfile)

        for line in infile:
            ir_str = line.strip()
            if not ir_str or len(ir_str) < 8:
                continue

            head = f"Cycle {pc}\n\nPC = {pc}\nIR = {ir_str}\n"
            try:
                a_log, s, s_d, co, n, z = ula_8bit_shifter(a_fixed, b_fixed, ir_str)
            except InvalidControlSignals:
                emit(head + f"> Error, invalid control signals.\n{SEP}\n", logfile)
                pc += 1
                continue

            emit(
                head
                + f"b = {b_fixed:032b}\n"
                f"a = {a_log:032b}\n"
                f"s = {s:032b}\n"
                f"sd = {s_d:032b}\n"
                f"n = {n}\n"
                f"z = {z}\n"
                f"co = {co}\n"
                f"{SEP}\n",
                logfile,
            )
            pc += 1

        emit(f"Cycle {pc}\n\nPC = {pc}\n> Line is empty, EOP.\n", logfile)


if __name__ == "__main__":
    args = sys.argv[1:]
    executar_tarefa1(*args[:2])
