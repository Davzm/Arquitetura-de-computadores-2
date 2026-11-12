# mic1.py
"""
Mic-1 modificada completa (Etapa 3): ULA + caminho de dados (reaproveitados da
Etapa 2, em etapa2/datapath.py) + memória de dados.

Microinstrução de 23 bits:  ULA(8) | C(9) | MEM(2) = [WRITE READ] | B(4)

Ordem de cada ciclo (exigida pelo PDF):
  1. ULA (A = H, B = registrador do barramento B);
  2. escrita de Sd nos registradores habilitados no barramento C;
  3. só então a memória (READ: MDR = mem[MAR]; WRITE: mem[MAR] = MDR).

Caso especial "fetch" (MEM = 11): os 8 primeiros bits são um byte de dado.
MBR = byte e H = MBR estendido com zeros; não passa pela ULA nem pelo
barramento C.
"""
import os
import shutil
import sys

# etapa2/ vai para o FIM do sys.path: só precisamos de `datapath` de lá, e os
# módulos de etapa3/ com o mesmo nome (ex.: tarefa1) devem ter prioridade.
_ETAPA2 = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "etapa2"))
if _ETAPA2 not in sys.path:
    sys.path.append(_ETAPA2)

from datapath import (  # noqa: E402
    MASK8, MASK32, InvalidControlSignals, Mic1DataPath,
)

STARS = "*" * 31
ERR_SIGNALS = "> Error, invalid control signals."
ERR_ADDRESS = "> Error, memory address out of range."


class Mic1(Mic1DataPath):
    def __init__(self):
        super().__init__()
        self.memory = []
        self.mem_file = None  # cópia de trabalho regravada após cada WRITE

    # ------------------------------------------------------------- memória
    def load_memory(self, data_path, work_path=None):
        """
        Carrega a memória de dados (uma palavra binária de 32 bits por linha,
        linhas vazias ignoradas, qualquer quantidade de linhas) e cria a cópia
        de trabalho `<nome>_execucao.txt`, que é a que será regravada. Assim o
        arquivo de entrada original nunca é alterado.
        """
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Arquivo de dados '{data_path}' não encontrado.")
        memory = []
        with open(data_path, "r", encoding="utf-8") as f:
            for num, line in enumerate(f, 1):
                word = line.strip()
                if not word:
                    continue
                if len(word) > 32 or set(word) - {"0", "1"}:
                    raise ValueError(f"{data_path}:{num}: palavra inválida "
                                     f"(esperado binário de até 32 bits): {word!r}")
                memory.append(int(word, 2))
        self.memory = memory

        if work_path is None:
            stem, _ = os.path.splitext(data_path)
            work_path = stem + "_execucao.txt"
        shutil.copyfile(data_path, work_path)
        self.mem_file = work_path

    def save_memory(self):
        if self.mem_file:
            with open(self.mem_file, "w", encoding="utf-8") as f:
                f.write(self.format_memory())

    def format_memory(self):
        return "".join(f"{w:032b}\n" for w in self.memory)

    # ------------------------------------------------------------ execução
    def execute(self, ir_str: str):
        """
        Executa uma microinstrução de 23 bits. Retorna um dict com:
          fetch (bool), b (nome do reg. no barramento B ou None),
          c (lista de regs do barramento C), errors (mensagens de erro).
        """
        result = {"fetch": False, "b": None, "c": [], "errors": []}
        if len(ir_str) != 23 or set(ir_str) - {"0", "1"}:
            raise ValueError(f"Microinstrução inválida (esperado 23 bits): {ir_str!r}")

        ula_ctrl = ir_str[0:8]
        c_code = int(ir_str[8:17], 2)
        write = ir_str[17] == "1"
        read = ir_str[18] == "1"
        b_code = int(ir_str[19:23], 2)

        # Caso especial: fetch (WRITE e READ em 1 ao mesmo tempo)
        if write and read:
            self.regs["MBR"] = int(ula_ctrl, 2) & MASK8
            self.regs["H"] = self.regs["MBR"]  # extensão com zeros para 32 bits
            result["fetch"] = True
            return result

        # 1 e 2. ULA e escrita no barramento C
        result["b"] = self.bus_b_name(b_code)
        result["c"] = self.decode_bus_c(c_code)
        try:
            self.run_alu_and_write_c(ula_ctrl, c_code, b_code)
        except InvalidControlSignals:
            result["errors"].append(ERR_SIGNALS)
            return result

        # 3. Memória, só depois do barramento C
        if read or write:
            addr = self.regs["MAR"]
            if addr >= len(self.memory):
                result["errors"].append(ERR_ADDRESS)
            elif read:
                self.regs["MDR"] = self.memory[addr] & MASK32
            else:
                self.memory[addr] = self.regs["MDR"] & MASK32
                self.save_memory()
        return result


def format_ir(ir_str: str) -> str:
    return f"{ir_str[0:8]} {ir_str[8:17]} {ir_str[17:19]} {ir_str[19:23]}"


def run_and_log(machine: Mic1, ir_str: str, emit):
    """Executa uma microinstrução e escreve no log ir, b, c e registradores."""
    regs_before = machine.format_registers()
    result = machine.execute(ir_str)

    out = [f"ir = {format_ir(ir_str)}"]
    if result["fetch"]:
        out.append(f"fetch: MBR = {machine.regs['MBR']:08b}, "
                   "H = MBR (zero-extended), ALU and C bus bypassed")
    else:
        out.append(f"b = {result['b'].lower()}")
        c = ", ".join(r.lower() for r in result["c"]) or "none"
        out.append(f"c = {c}")
    out.extend(result["errors"])
    emit("\n".join(out) + "\n\n")
    emit(f"> Registers before instruction\n{STARS}\n{regs_before}\n")
    emit(f"> Registers after instruction\n{STARS}\n{machine.format_registers()}")
    return result
