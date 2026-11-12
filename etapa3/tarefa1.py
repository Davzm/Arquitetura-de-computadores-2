# etapa3_tarefa1.py
"""
Etapa 3 - Tarefa 1: executor de microinstruções de 23 bits com memória de dados.

Uso:
    python3 etapa3/tarefa1.py [microinstrucoes.txt] [registradores.txt] [dados.txt] [log.txt]

Sem argumentos, usa os arquivos `microinstruções_etapa3_tarefa1.txt`,
`registradores_etapa3_tarefa1.txt` e `dados_etapa3_tarefa1.txt` desta pasta e
grava `log_etapa3_tarefa1.txt`. A memória é regravada na cópia
`<dados>_execucao.txt` (também nesta pasta); o arquivo de dados original não muda.
"""
import os
import sys

from mic1 import STARS, Mic1, run_and_log

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEP = "=" * 60


def executar_tarefa1(micro_file=None, reg_file=None, data_file=None, log_file=None,
                     work_mem_file=None, echo=True):
    micro_file = micro_file or os.path.join(BASE_DIR, "microinstruções_etapa3_tarefa1.txt")
    reg_file = reg_file or os.path.join(BASE_DIR, "registradores_etapa3_tarefa1.txt")
    data_file = data_file or os.path.join(BASE_DIR, "dados_etapa3_tarefa1.txt")
    log_file = log_file or os.path.join(BASE_DIR, "log_etapa3_tarefa1.txt")
    if work_mem_file is None:
        stem = os.path.splitext(os.path.basename(data_file))[0]
        work_mem_file = os.path.join(BASE_DIR, stem + "_execucao.txt")

    machine = Mic1()
    machine.load_initial_registers(reg_file)
    machine.load_memory(data_file, work_mem_file)

    with open(micro_file, "r", encoding="utf-8") as f:
        program = [line.strip() for line in f if line.strip()]

    with open(log_file, "w", encoding="utf-8") as logfile:
        def emit(text):
            if echo:
                print(text, end="")
            logfile.write(text)

        emit(f"{SEP}\nInitial memory state\n{STARS}\n{machine.format_memory()}")
        emit(f"{STARS}\nInitial register state\n{STARS}\n{machine.format_registers()}")
        emit(f"{SEP}\nStart of Program\n{SEP}\n")

        cycle = 1
        for ir_str in program:
            emit(f"Cycle {cycle}\n")
            try:
                run_and_log(machine, ir_str, emit)
            except ValueError as exc:
                emit(f"> Error, {exc}\n{SEP}\n")
                cycle += 1
                continue
            emit(f"\n> Memory after instruction\n{STARS}\n{machine.format_memory()}{SEP}\n")
            cycle += 1

        emit(f"Cycle {cycle}\nNo more lines, EOP.\n")
    return machine


if __name__ == "__main__":
    executar_tarefa1(*sys.argv[1:5])
