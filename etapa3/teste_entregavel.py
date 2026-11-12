# teste_entregavel.py
"""
Testes da Etapa 3 (sem dependências externas).

Uso:
    python3 etapa3/teste_entregavel.py

Os logs e a cópia de trabalho da memória são gravados em um diretório
temporário, então os arquivos de entrada e os logs da pasta não são alterados.
"""
import os
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from entregavel import parse_line, parse_program, run_program  # noqa: E402
from tarefa1 import executar_tarefa1  # noqa: E402

REGS = os.path.join(BASE_DIR, "registradores_etapa3_tarefa1.txt")
DADOS = os.path.join(BASE_DIR, "dados_etapa3_tarefa1.txt")
INSTR = os.path.join(BASE_DIR, "instruções.txt")
MICRO = os.path.join(BASE_DIR, "microinstruções_etapa3_tarefa1.txt")


def _write(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def test_entregavel_caso_a():
    """BIPUSH 00110011 / DUP / ILOAD 1 com os arquivos oficiais."""
    with open(DADOS, encoding="utf-8") as f:
        dados_originais = f.read()
    with tempfile.TemporaryDirectory() as tmp:
        work = os.path.join(tmp, "dados_execucao.txt")
        m = run_program(INSTR, REGS, DADOS, os.path.join(tmp, "log.txt"),
                        work_mem_file=work, echo=False)
        r = m.regs
        assert r["SP"] == 10, r["SP"]
        assert r["MAR"] == 10, r["MAR"]
        assert r["MDR"] == 2, r["MDR"]
        assert r["TOS"] == 2, r["TOS"]
        assert r["H"] == 3, r["H"]
        assert r["LV"] == 2, r["LV"]
        assert r["MBR"] == 0b00110011, r["MBR"]
        assert r["PC"] == 0 and r["CPP"] == 0 and r["OPC"] == 0
        esperado = [0, 0, 1, 2, 4, 8, 16, 32, 0x33, 0x33, 2, 0, 0, 0, 0, 0]
        assert m.memory == esperado, m.memory
        # A cópia de trabalho foi regravada; o arquivo original não.
        with open(work, encoding="utf-8") as f:
            assert [int(x, 2) for x in f.read().split()] == esperado
    with open(DADOS, encoding="utf-8") as f:
        assert f.read() == dados_originais


def test_entregavel_estados_intermediarios():
    """Confere o estado após cada instrução IJVM do caso A."""
    with tempfile.TemporaryDirectory() as tmp:
        work = os.path.join(tmp, "w.txt")
        estados = []
        for n, prog in enumerate((["BIPUSH 00110011"],
                                  ["BIPUSH 00110011", "DUP"])):
            p = os.path.join(tmp, f"p{n}.txt")
            _write(p, prog)
            m = run_program(p, REGS, DADOS, os.path.join(tmp, "l.txt"),
                            work_mem_file=work, echo=False)
            estados.append(m)
        b, d = estados
        assert (b.regs["SP"], b.regs["MAR"], b.regs["MBR"], b.regs["H"],
                b.regs["MDR"], b.regs["TOS"]) == (8, 8, 0x33, 0x33, 0x33, 0x33)
        assert b.memory[8] == 0x33
        assert (d.regs["SP"], d.regs["MAR"], d.regs["MDR"]) == (9, 9, 0x33)
        assert d.memory[9] == 0x33


def test_rejeita_instrucoes_invalidas():
    assert parse_line("iload 0")[:2] == ("ILOAD", 0)
    assert parse_line("dup")[:2] == ("DUP", None)
    assert parse_line("Bipush 11111111")[:2] == ("BIPUSH", "11111111")
    for ruim in ("IADD", "ILOAD", "ILOAD -1", "ILOAD x", "ILOAD 1 2", "DUP 1",
                 "BIPUSH 0011", "BIPUSH 51", "BIPUSH 001100112", "BIPUSH"):
        try:
            parse_line(ruim)
        except ValueError:
            continue
        raise AssertionError(f"deveria rejeitar {ruim!r}")
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "p.txt")
        _write(p, ["DUP", "", "FOO 1"])
        try:
            parse_program(p)
        except ValueError as exc:
            assert ":3:" in str(exc)
        else:
            raise AssertionError("programa inválido aceito")


def test_tarefa1_arquivos_oficiais():
    """Caso B: ciclo 1 SP=8, MDR=mem[0]=0; ciclo 2 MAR=8, mem[8]=0."""
    with tempfile.TemporaryDirectory() as tmp:
        m = executar_tarefa1(MICRO, REGS, DADOS, os.path.join(tmp, "log.txt"),
                             work_mem_file=os.path.join(tmp, "w.txt"), echo=False)
        assert m.regs["SP"] == 8 and m.regs["MAR"] == 8 and m.regs["MDR"] == 0
        assert m.memory[8] == 0


def test_tarefa1_estado_do_exemplo():
    """Caso C: estado inicial de saída_etapa3_tarefa1 (mar=sp=4, mem[4]=2)."""
    with tempfile.TemporaryDirectory() as tmp:
        regs = os.path.join(tmp, "r.txt")
        dados = os.path.join(tmp, "d.txt")
        _write(regs, [f"{n} = {'0' * 29 + '100' if n in ('mar', 'sp') else '0' * 32}"
                      for n in ("mar", "mdr", "pc", "sp", "lv", "cpp", "tos", "opc", "h")]
               + ["mbr = 00000000"])
        _write(dados, [f"{2 if i == 4 else 0:032b}" for i in range(16)])
        m = executar_tarefa1(MICRO, regs, dados, os.path.join(tmp, "log.txt"),
                             work_mem_file=os.path.join(tmp, "w.txt"), echo=False)
        assert m.regs["SP"] == 5 and m.regs["MAR"] == 5 and m.regs["MDR"] == 2
        assert m.memory == [0, 0, 0, 0, 2, 2] + [0] * 10


if __name__ == "__main__":
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    falhas = 0
    for t in testes:
        try:
            t()
            print(f"OK    {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            falhas += 1
            print(f"FALHA {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(testes) - falhas}/{len(testes)} testes passaram.")
    sys.exit(1 if falhas else 0)
