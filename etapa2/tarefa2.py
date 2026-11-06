# etapa2_tarefa2.py
import os

REG_NAMES_32 = ["MAR", "MDR", "PC", "SP", "LV", "CPP", "TOS", "OPC", "H"]
BUS_B_MAP = {
    0: "MDR", 1: "PC", 2: "MBR", 3: "MBRU",
    4: "SP",  5: "LV", 6: "CPP", 7: "TOS", 8: "OPC"
}
BUS_C_MAP = [
    (8, "H"), (7, "OPC"), (6, "TOS"), (5, "CPP"), (4, "LV"),
    (3, "SP"), (2, "PC"), (1, "MDR"), (0, "MAR")
]

class Mic1DataPath:
    def __init__(self):
        self.regs = {name: 0 for name in REG_NAMES_32}
        self.regs["MBR"] = 0  # 8 bits

    def load_initial_registers(self, filepath="registradores_etapa2_tarefa2.txt"):
        if not os.path.exists(filepath):
            return
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    k, v = line.split("=")
                    k, v = k.strip(), v.strip()
                    val = int(v, 2) if set(v).issubset({'0', '1'}) else int(v)
                    if k in self.regs:
                        self.regs[k] = val

    def get_bus_b_value(self, b_code: int):
        reg_name = BUS_B_MAP.get(b_code, "MDR")
        if reg_name == "MBR":  # Extensão de sinal
            val = self.regs["MBR"] & 0xFF
            return val if val < 128 else val - 256
        elif reg_name == "MBRU":  # Extensão com zeros
            return self.regs["MBR"] & 0xFF
        else:
            return self.regs.get(reg_name, 0) & 0xFFFFFFFF

    def execute_instruction(self, ir_str: str):
        # Separa os 21 bits: [8 bits ULA | 9 bits Bus C | 4 bits Bus B]
        ula_ctrl_str = ir_str[0:8]
        c_bus_str = ir_str[8:17]
        b_bus_str = ir_str[17:21]

        b_code = int(b_bus_str, 2)
        c_code = int(c_bus_str, 2)

        # Entrada A = H, Entrada B = Registrador selecionado no Decodificador
        a_in = self.regs["H"]
        b_in = self.get_bus_b_value(b_code)

        # Sinais da ULA
        sll8 = int(ula_ctrl_str[0])
        sra1 = int(ula_ctrl_str[1])
        f0   = int(ula_ctrl_str[2])
        f1   = int(ula_ctrl_str[3])
        ena  = int(ula_ctrl_str[4])
        enb  = int(ula_ctrl_str[5])
        inva = int(ula_ctrl_str[6])
        inc  = int(ula_ctrl_str[7])

        a_prime = a_in if ena == 1 else 0
        b_prime = b_in if enb == 1 else 0
        a_op = (~a_prime & 0xFFFFFFFF) if inva == 1 else a_prime

        op = (f0 << 1) | f1
        if op == 0:   res = a_op & b_prime
        elif op == 1: res = a_op | b_prime
        elif op == 2: res = (~b_prime) & 0xFFFFFFFF
        else:         res = (a_op + b_prime + inc) & 0xFFFFFFFF

        # Deslocador
        if sll8 == 1:
            s_d = (res << 8) & 0xFFFFFFFF
        elif sra1 == 1:
            s_signed = res if res < 0x80000000 else res - 0x100000000
            s_d = (s_signed >> 1) & 0xFFFFFFFF
        else:
            s_d = res & 0xFFFFFFFF

        # Identifica registradores ativados no Barramento C
        enabled_c_regs = []
        for bit_pos, reg_name in BUS_C_MAP:
            if (c_code >> bit_pos) & 1:
                enabled_c_regs.append(reg_name)

        # Atualiza os registradores habilitados
        for reg_name in enabled_c_regs:
            if reg_name == "MBR":
                self.regs[reg_name] = s_d & 0xFF
            else:
                self.regs[reg_name] = s_d & 0xFFFFFFFF

        return BUS_B_MAP.get(b_code, "MDR"), enabled_c_regs


def rodar_simulacao_tarefa2(prog_file="programa_etapa2_tarefa2.txt",
                             reg_file="registradores_etapa2_tarefa2.txt",
                             log_file="log_etapa2_tarefa2.txt"):
    datapath = Mic1DataPath()
    datapath.load_initial_registers(reg_file)

    if not os.path.exists(prog_file):
        print(f"Erro: Arquivo '{prog_file}' não encontrado.")
        return

    with open(prog_file, "r") as infile, open(log_file, "w") as logfile:
        logfile.write("=== Inicio do Programa Etapa 2 Tarefa 2 ===\n\n")

        inst_num = 1
        for line in infile:
            ir_str = line.strip()
            if not ir_str or len(ir_str) < 21:
                continue

            regs_before = {k: f"0x{v:08X}" for k, v in datapath.regs.items()}
            bus_b_reg, bus_c_regs = datapath.execute_instruction(ir_str)
            regs_after = {k: f"0x{v:08X}" for k, v in datapath.regs.items()}

            log_entry = (
                f"--- Instrucao {inst_num} ---\n"
                f"IR: {ir_str}\n"
                f"Barramento B comanda: {bus_b_reg}\n"
                f"Barramento C escreve em: {', '.join(bus_c_regs) if bus_c_regs else 'Nenhum'}\n"
                f"Registradores Inicio: {regs_before}\n"
                f"Registradores Fim:    {regs_after}\n"
                + "="*60 + "\n"
            )
            print(log_entry, end="")
            logfile.write(log_entry)
            inst_num += 1

if __name__ == "__main__":
    rodar_simulacao_tarefa2()
