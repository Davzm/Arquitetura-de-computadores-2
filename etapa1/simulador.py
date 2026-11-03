import os

def ula_32bit(a_fixed: int, b_fixed: int, ir_str: str):
    """
    Simula a ULA de 32 bits do Mic-1.
    Sinais em ir_str (6 bits): [F0, F1, ENA, ENB, INVA, INC]
    """
    f0   = int(ir_str[0])
    f1   = int(ir_str[1])
    ena  = int(ir_str[2])
    enb  = int(ir_str[3])
    inva = int(ir_str[4])
    inc  = int(ir_str[5])

    # 1. Habilita/Desabilita entradas A e B
    a_prime = a_fixed if ena == 1 else 0
    b_prime = b_fixed if enb == 1 else 0

    # O valor impresso para 'a' no log reflete o sinal pós-ENA
    a_log = a_prime

    # 2. Inversão de A (bitwise NOT de 32 bits)
    a_op = (~a_prime & 0xFFFFFFFF) if inva == 1 else a_prime

    # 3. Executa a operação lógica/aritmética (F0, F1)
    op = (f0 << 1) | f1
    co = 0

    if op == 0:      # 00: A AND B
        s = a_op & b_prime
    elif op == 1:    # 01: A OR B
        s = a_op | b_prime
    elif op == 2:    # 10: NOT B
        s = (~b_prime) & 0xFFFFFFFF
    elif op == 3:    # 11: Soma A + B + INC
        res = a_op + b_prime + inc
        s = res & 0xFFFFFFFF
        co = 1 if res > 0xFFFFFFFF else 0
    else:
        s = 0

    return a_log, s, co


def executar_etapa1(input_file="programa_etapa1.txt", log_file="log_etapa1.txt"):
    # Entradas A e B permanecem fixas durante toda a Etapa 1
    a_fixed = 0xFFFFFFFF  # 32 uns
    b_fixed = 0x00000001  # 1

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
            if not ir_str or len(ir_str) < 6:
                continue

            a_log, s_val, co = ula_32bit(a_fixed, b_fixed, ir_str)

            cycle_log = (
                f"Cycle {pc}\n\n"
                f"PC = {pc}\n"
                f"IR = {ir_str}\n"
                f"b = {b_fixed:032b}\n"
                f"a = {a_log:032b}\n"
                f"s = {s_val:032b}\n"
                f"co = {co}\n"
                + "="*60 + "\n"
            )

            print(cycle_log, end="")
            logfile.write(cycle_log)

            pc += 1

        end_log = f"Cycle {pc}\n\nPC = {pc}\n> Line is empty, EOP.\n"
        print(end_log, end="")
        logfile.write(end_log)

    print(f"\nExecução concluída! Log salvo em '{log_file}'.")

if __name__ == "__main__":
    executar_etapa1()
