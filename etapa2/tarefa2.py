# etapa2_tarefa2.py
"""
Etapa 2 - Tarefa 2: caminho de dados da Mic-1 com microinstruções de 21 bits
[ULA(8) | C(9) | B(4)].

Uso:
    python3 etapa2/tarefa2.py [programa.txt] [registradores.txt] [log.txt]

Sem argumentos, usa `programa_etapa2_tarefa2.txt`, `registradores_etapa2_tarefa2.txt`
e grava `log_etapa2_tarefa2.txt`, todos na pasta deste arquivo.
"""
import os
import sys

# A ULA e o caminho de dados ficam no módulo compartilhado (reusado na Etapa 3)
from datapath import InvalidControlSignals, Mic1DataPath

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEP = "=" * 53


def rodar_simulacao_tarefa2(prog_file=None, reg_file=None, log_file=None):
    prog_file = prog_file or os.path.join(BASE_DIR, "programa_etapa2_tarefa2.txt")
    reg_file = reg_file or os.path.join(BASE_DIR, "registradores_etapa2_tarefa2.txt")
    log_file = log_file or os.path.join(BASE_DIR, "log_etapa2_tarefa2.txt")

    if not os.path.exists(prog_file):
        print(f"Erro: Arquivo '{prog_file}' não encontrado.")
        return

    datapath = Mic1DataPath()
    datapath.load_initial_registers(reg_file)

    with open(prog_file, "r") as infile:
        program = [line.strip() for line in infile if line.strip()]

    with open(log_file, "w") as logfile:
        def emit(text):
            print(text, end="")
            logfile.write(text)

        emit("\n".join(program) + "\n\n")
        emit(f"{SEP}\n> Initial register states\n")
        emit(datapath.format_registers())
        emit(f"\n{SEP}\nStart of program\n{SEP}\n")

        cycle = 1
        for ir_str in program:
            if len(ir_str) != 21 or set(ir_str) - {"0", "1"}:
                emit(f"Cycle {cycle}\nir = {ir_str}\n> Error, invalid instruction "
                     f"(expected 21 bits).\n{SEP}\n")
                cycle += 1
                continue

            emit(f"Cycle {cycle}\nir = {ir_str[0:8]} {ir_str[8:17]} {ir_str[17:21]}\n\n")
            regs_before = datapath.format_registers()
            try:
                bus_b_reg, bus_c_regs = datapath.execute_instruction(ir_str)
            except InvalidControlSignals:
                emit(f"> Error, invalid control signals.\n{SEP}\n")
                cycle += 1
                continue

            c_text = ", ".join(r.lower() for r in bus_c_regs) if bus_c_regs else "none"
            emit(
                f"b_bus = {bus_b_reg.lower()}\n"
                f"c_bus = {c_text}\n\n"
                f"> Registers before instruction\n{regs_before}\n"
                f"> Registers after instruction\n{datapath.format_registers()}"
                f"{SEP}\n"
            )
            cycle += 1

        emit(f"Cycle {cycle}\nNo more lines, EOP.\n")


if __name__ == "__main__":
    rodar_simulacao_tarefa2(*sys.argv[1:4])
