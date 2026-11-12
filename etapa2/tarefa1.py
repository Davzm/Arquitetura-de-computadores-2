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

SEP = "=" * 60
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# A ULA fica no módulo compartilhado (também usado pela Tarefa 2 e Etapa 3)
from datapath import InvalidControlSignals, ula_8bit_shifter  # noqa: E402


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
