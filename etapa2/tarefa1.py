# etapa2_tarefa1.py
import os

def ula_8bit_shifter(a_val: int, b_val: int, ir_str: str):
    """
    ULA de 8 bits com Deslocador e Flags N/Z.
    IR (8 bits): [SLL8, SRA1, F0, F1, ENA, ENB, INVA, INC]
    """
    sll8 = int(ir_str[0])
    sra1 = int(ir_str[1])
    f0   = int(ir_str[2])
    f1   = int(ir_str[3])
    ena  = int(ir_str[4])
    enb  = int(ir_str[5])
    inva = int(ir_str[6])
    inc  = int(ir_str[7])

    # 1. Habilitação das entradas
    a_prime = a_val if ena == 1 else 0
    b_prime = b_val if enb == 1 else 0

    # 2. Inversão de A
    a_op = (~a_prime & 0xFFFFFFFF) if inva == 1 else a_prime

    # 3. Operação Principal da ULA
    op = (f0 << 1) | f1
    co = 0

    if op == 0:      # 00: AND
        s = a_op & b_prime
    elif op == 1:    # 01: OR
        s = a_op | b_prime
    elif op == 2:    # 10: NOT B
        s = (~b_prime) & 0xFFFFFFFF
    elif op == 3:    # 11: Addition
        res = a_op + b_prime + inc
        s = res & 0xFFFFFFFF
        co = 1 if res > 0xFFFFFFFF else 0
    else:
        s = 0

    # 4. Deslocador (Shifter)
    if sll8 == 1:
        s_d = (s << 8) & 0xFFFFFFFF
    elif sra1 == 1:
        # Deslocamento aritmético à direita (preserva o bit de sinal de 32 bits)
        s_signed = s if s < 0x80000000 else s - 0x100000000
        s_d = (s_signed >> 1) & 0xFFFFFFFF
    else:
        s_d = s

    # 5. Flags N e Z
    z = 1 if s_d == 0 else 0
    n = 1 if (s_d & 0x80000000) != 0 else 0

    return a_prime, s_d, co, n, z


def executar_tarefa1(input_file="programa_etapa2_tarefa1.txt", log_file="log_etapa2_tarefa1.txt"):
    a_fixed = 0xFFFFFFFF
    b_fixed = 0x00000001
    pc = 1

    if not os.path.exists(input_file):
        print(f"Erro: Arquivo '{input_file}' não encontrado.")
        return

    with open(input_file, "r") as infile, open(log_file, "w") as logfile:
        header = f"b = {b_fixed:032b}\na = {a_fixed:032b}\n\nStart of Program\n" + "="*60 + "\n"
        print(header, end="")
        logfile.write(header)

        for line in infile:
            ir_str = line.strip()
            if not ir_str or len(ir_str) < 8:
                continue

            a_log, s_d, co, n, z = ula_8bit_shifter(a_fixed, b_fixed, ir_str)

            cycle_log = (
                f"Cycle {pc}\n\n"
                f"PC = {pc}\n"
                f"IR = {ir_str}\n"
                f"b = {b_fixed:032b}\n"
                f"a = {a_log:032b}\n"
                f"s_d = {s_d:032b}\n"
                f"co = {co}, N = {n}, Z = {z}\n"
                + "="*60 + "\n"
            )
            print(cycle_log, end="")
            logfile.write(cycle_log)
            pc += 1

        end_log = f"Cycle {pc}\n\nPC = {pc}\n> Line is empty, EOP.\n"
        print(end_log, end="")
        logfile.write(end_log)

if __name__ == "__main__":
    executar_tarefa1()
