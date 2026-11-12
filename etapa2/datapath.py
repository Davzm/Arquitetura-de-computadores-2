# datapath.py
"""
Módulo reutilizável da Mic-1 modificada: ULA de 8 sinais com deslocador e
caminho de dados (registradores, barramento B e barramento C).

Usado por etapa2/tarefa1.py, etapa2/tarefa2.py e etapa3/mic1.py.
"""
import os

MASK32 = 0xFFFFFFFF
MASK8 = 0xFF


class InvalidControlSignals(Exception):
    """SLL8 e SRA1 ativos ao mesmo tempo (proibido pelo PDF)."""


def ula_8bit_shifter(a_val: int, b_val: int, ir_str: str):
    """
    ULA de 8 bits com Deslocador e Flags N/Z.
    IR (8 bits): [SLL8, SRA1, F0, F1, ENA, ENB, INVA, INC]

    Retorna (a_prime, s, s_d, co, n, z), onde s é a saída da ULA antes do
    deslocador e s_d é a saída deslocada. Lança InvalidControlSignals se
    SLL8 e SRA1 estiverem ambos em 1.
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


# Ordem de impressão dos registradores nos logs (igual aos exemplos oficiais)
LOG_ORDER = ["MAR", "MDR", "PC", "MBR", "SP", "LV", "CPP", "TOS", "OPC", "H"]
REG_NAMES_32 = ["MAR", "MDR", "PC", "SP", "LV", "CPP", "TOS", "OPC", "H"]

# Decodificador de 4 bits do barramento B
BUS_B_MAP = {
    0: "MDR", 1: "PC", 2: "MBR", 3: "MBRU",
    4: "SP",  5: "LV", 6: "CPP", 7: "TOS", 8: "OPC"
}
# Seletor de 9 bits do barramento C (bit, registrador), do MSB ao LSB
BUS_C_MAP = [
    (8, "H"), (7, "OPC"), (6, "TOS"), (5, "CPP"), (4, "LV"),
    (3, "SP"), (2, "PC"), (1, "MDR"), (0, "MAR")
]


class Mic1DataPath:
    def __init__(self):
        self.regs = {name: 0 for name in REG_NAMES_32}
        self.regs["MBR"] = 0  # 8 bits

    def load_initial_registers(self, filepath):
        """
        Lê linhas `nome = valor`. Nomes sem diferenciar maiúsculas/minúsculas;
        valores SEMPRE em binário (formato oficial).
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Arquivo de registradores '{filepath}' não encontrado.")
        with open(filepath, "r", encoding="utf-8") as f:
            for num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                if "=" not in line:
                    raise ValueError(f"{filepath}:{num}: linha inválida: {line!r}")
                k, v = (part.strip() for part in line.split("=", 1))
                name = k.upper()
                if name not in self.regs:
                    raise ValueError(f"{filepath}:{num}: registrador desconhecido: {k!r}")
                try:
                    val = int(v, 2)
                except ValueError:
                    raise ValueError(f"{filepath}:{num}: valor não é binário: {v!r}") from None
                self.regs[name] = val & (MASK8 if name == "MBR" else MASK32)

    def get_bus_b_value(self, b_code: int):
        reg_name = BUS_B_MAP.get(b_code, "MDR")
        if reg_name == "MBR":  # Extensão de sinal
            val = self.regs["MBR"] & MASK8
            return (val | 0xFFFFFF00) if val & 0x80 else val
        elif reg_name == "MBRU":  # Extensão com zeros
            return self.regs["MBR"] & MASK8
        else:
            return self.regs[reg_name] & MASK32

    def bus_b_name(self, b_code: int):
        return BUS_B_MAP.get(b_code, "MDR")

    @staticmethod
    def decode_bus_c(c_code: int):
        return [name for bit, name in BUS_C_MAP if (c_code >> bit) & 1]

    def run_alu_and_write_c(self, ula_ctrl_str: str, c_code: int, b_code: int):
        """
        Executa a ULA (A = H, B = registrador do barramento B) e, só depois,
        escreve Sd nos registradores habilitados no barramento C.
        Retorna (nome_reg_B, lista_regs_C).
        """
        a_in = self.regs["H"]
        b_in = self.get_bus_b_value(b_code)
        _, _, s_d, _, _, _ = ula_8bit_shifter(a_in, b_in, ula_ctrl_str)

        enabled_c_regs = self.decode_bus_c(c_code)
        for reg_name in enabled_c_regs:
            self.regs[reg_name] = s_d & MASK32

        return self.bus_b_name(b_code), enabled_c_regs

    def execute_instruction(self, ir_str: str):
        # Separa os 21 bits: [8 bits ULA | 9 bits Bus C | 4 bits Bus B]
        ula_ctrl_str = ir_str[0:8]
        c_code = int(ir_str[8:17], 2)
        b_code = int(ir_str[17:21], 2)
        return self.run_alu_and_write_c(ula_ctrl_str, c_code, b_code)

    def format_registers(self):
        """Registradores em binário, um por linha (mbr em 8 bits, demais 32)."""
        lines = []
        for name in LOG_ORDER:
            width = 8 if name == "MBR" else 32
            lines.append(f"{name.lower()} = {self.regs[name]:0{width}b}")
        return "\n".join(lines) + "\n"
