# Arquitetura-de-computadores-2

Grupo: Davi Oliveira Malheiros, Alexandre Lacerda Fernandes Silva e Matheus Gomes Félix da Silva

Simulador da Mic-1 modificada (Arquitetura de Computadores II – UFPB), em
Python 3, sem dependências externas. A especificação é o PDF
`exemplos_oficiais/Projeto_2026.2 (1).pdf`; os arquivos de teste oficiais
estão em `exemplos_oficiais/exemplos_projeto 2/`.

## Estrutura de pastas

```
etapa1/
  simulador.py                     ULA de 6 sinais (Etapa 1)
  programa_etapa1.txt              entrada
  log_etapa1.txt                   saída gerada
etapa2/
  datapath.py                      módulo compartilhado: ULA de 8 sinais com
                                   deslocador + caminho de dados (Mic1DataPath)
  tarefa1.py                       Tarefa 1: ULA com SLL8/SRA1 e flags N/Z
  tarefa2.py                       Tarefa 2: caminho de dados, microinstruções de 21 bits
  programa_etapa2_tarefa1.txt      entrada da Tarefa 1 (programa do grupo)
  programa_etapa2_tarefa2.txt      entrada da Tarefa 2 (programa do grupo)
  registradores_etapa2_tarefa2.txt registradores iniciais (formato oficial, binário)
  log_etapa2_tarefa1.txt           saídas geradas
  log_etapa2_tarefa2.txt
etapa3/
  mic1.py                          máquina completa: caminho de dados + memória,
                                   microinstruções de 23 bits, fetch
  tarefa1.py                       Tarefa 1: executor de microinstruções de 23 bits
  entregavel.py                    ENTREGÁVEL: traduz e executa ILOAD x, DUP, BIPUSH b
  teste_entregavel.py              testes automatizados (asserts)
  instruções.txt                   entradas (cópias dos arquivos oficiais)
  microinstruções_etapa3_tarefa1.txt
  registradores_etapa3_tarefa1.txt
  dados_etapa3_tarefa1.txt
  log_etapa3_tarefa1.txt           saídas geradas
  log_entregavel.txt
exemplos_oficiais/                 PDF e arquivos de teste fornecidos pela professora
```

## Como rodar

Todos os scripts das Etapas 2 e 3 procuram as entradas na própria pasta do
script (podem ser executados de qualquer diretório) e aceitam os caminhos
como argumentos opcionais. Os logs também são impressos no terminal.

### Etapa 1

```sh
cd etapa1 && python3 simulador.py
```
Entrada: `programa_etapa1.txt`. Saída: `log_etapa1.txt`.

### Etapa 2 – Tarefa 1 (ULA com deslocador)

```sh
python3 etapa2/tarefa1.py [programa.txt] [log.txt]
# teste oficial:
python3 etapa2/tarefa1.py "exemplos_oficiais/exemplos_projeto 2/programa_etapa2_tarefa1.txt"
```
As entradas fixas `A` e `B` são constantes no topo de `etapa2/tarefa1.py`
(padrão do teste oficial: `A = 0x00000001`, `B = 0x80000000`).
Saída padrão: `etapa2/log_etapa2_tarefa1.txt`.

### Etapa 2 – Tarefa 2 (caminho de dados, 21 bits)

```sh
python3 etapa2/tarefa2.py [programa.txt] [registradores.txt] [log.txt]
# teste oficial:
python3 etapa2/tarefa2.py "exemplos_oficiais/exemplos_projeto 2/programa_etapa2_tarefa2.txt" \
                          "exemplos_oficiais/exemplos_projeto 2/registradores_etapa2_tarefa2.txt"
```
Arquivo de registradores: linhas `nome = valor`, nome em maiúsculas ou
minúsculas, valor **sempre em binário** (mbr com 8 bits, demais com 32).
Saída padrão: `etapa2/log_etapa2_tarefa2.txt`.

### Etapa 3 – Tarefa 1 (microinstruções de 23 bits com memória)

```sh
python3 etapa3/tarefa1.py [microinstruções.txt] [registradores.txt] [dados.txt] [log.txt]
```
Padrão: `microinstruções_etapa3_tarefa1.txt`, `registradores_etapa3_tarefa1.txt`
e `dados_etapa3_tarefa1.txt` de `etapa3/`. Saída: `etapa3/log_etapa3_tarefa1.txt`.

### Entregável (instruções IJVM)

```sh
python3 etapa3/entregavel.py [instruções.txt] [registradores.txt] [dados.txt] [log.txt]
```
Padrão: `instruções.txt`, `registradores_etapa3_tarefa1.txt` e
`dados_etapa3_tarefa1.txt` de `etapa3/`. Saída: `etapa3/log_entregavel.txt`.

Formato de `instruções.txt` (uma por linha; linhas vazias ignoradas;
maiúsculas/minúsculas indiferentes):

```
BIPUSH 00110011     byte de 8 bits em binário
DUP
ILOAD 1             índice decimal >= 0
```
O arquivo é validado inteiro antes da execução; instruções desconhecidas ou
argumentos inválidos são rejeitados com mensagem indicando a linha.

Para a avaliação, basta substituir os três arquivos de entrada em `etapa3/`
(ou passar os caminhos na linha de comando).

**Memória de dados:** uma palavra binária de 32 bits por linha (qualquer
quantidade de linhas; o endereço é o índice da linha a partir de 0). O PDF
exige que o arquivo de dados seja regravado a cada WRITE; para não destruir as
entradas de teste, o programa copia o arquivo para `<nome>_execucao.txt`
(em `etapa3/`) no início e regrava essa cópia. Acesso com MAR fora do intervalo
gera `> Error, memory address out of range.` e a operação de memória é ignorada.

### Testes

```sh
python3 etapa3/teste_entregavel.py
```
Executa o entregável com os arquivos oficiais (`BIPUSH 00110011`, `DUP`,
`ILOAD 1`) e confere o estado final (SP=MAR=10, MDR=TOS=2, H=3, LV=2,
MBR=00110011, mem = [0,0,1,2,4,8,16,32,0x33,0x33,2,0,…]), além da validação de
entrada e da Tarefa 1 da Etapa 3.

## Decisões de implementação

- ULA: sinais `[SLL8 SRA1 F0 F1 ENA ENB INVA INC]`; F0F1 = 00 AND, 01 OR,
  10 NOT B, 11 A+B+INC; deslocador depois da ULA; tudo mascarado em 32 bits;
  N e Z calculados sobre a saída deslocada Sd. SLL8 e SRA1 juntos geram
  `> Error, invalid control signals.` e a microinstrução não é executada.
- Barramento B: 0 MDR, 1 PC, 2 MBR (extensão de sinal), 3 MBRU (extensão com
  zeros), 4 SP, 5 LV, 6 CPP, 7 TOS, 8 OPC. Barramento C (bit 8 → 0): H, OPC,
  TOS, CPP, LV, SP, PC, MDR, MAR. Entrada A é sempre H.
- Ciclo da Etapa 3: ULA → escrita no barramento C → memória (READ:
  MDR = mem[MAR]; WRITE: mem[MAR] = MDR).
- `fetch` (MEM = 11): os 8 primeiros bits são o byte; MBR = byte e
  H = MBR estendido com zeros, sem ULA e sem barramento C.
- Microinstruções do entregável (ULA | C | MEM | B):

  | Microinstrução | ULA | C | MEM | B |
  |---|---|---|---|---|
  | `H = LV` | 00110100 | 100000000 | 00 | 0101 |
  | `H = H+1` | 00111001 | 100000000 | 00 | 0000 |
  | `MAR = H; rd` | 00111000 | 000000001 | 01 | 0000 |
  | `MAR = SP = SP+1; wr` | 00110101 | 000001001 | 10 | 0100 |
  | `MAR = SP = SP+1` | 00110101 | 000001001 | 00 | 0100 |
  | `TOS = MDR` | 00110100 | 001000000 | 00 | 0000 |
  | `MDR = TOS; wr` | 00110100 | 000000010 | 10 | 0111 |
  | `fetch` | byte | 000000000 | 11 | 0000 |
  | `MDR = TOS = H; wr` | 00111000 | 001000010 | 10 | 0000 |

## Divergências entre os exemplos oficiais e o PDF

O PDF é a regra. Os itens abaixo são erros dos arquivos de exemplo e **não**
são reproduzidos pelo simulador.

- **`saída_etapa1.txt`**: mostra `IR = 111100` no ciclo 1, mas
  `programa_etapa1.txt` tem `111110`.
- **`saída_etapa2_tarefa1.txt`**:
  - ciclo 1 mostra `sd = 0x200`, mas o correto é `0x80000001 << 8 = 0x100`
    (deslocamento lógico de 8 bits, mascarado em 32 bits);
  - ciclo 2 mostra `n = 0` com `sd = 0xC0000000`, mas o bit 31 de Sd é 1, logo
    o correto é `n = 1`.
- **`saída_etapa2_tarefa2.txt`**:
  - MBR e MBRU estão invertidos: o exemplo estende `mbr` com zeros (código 2)
    e `mbru` com sinal (código 3); pelo PDF, código 2 = MBR com sinal
    (ciclo 1: LV = SP = `0xFFFFFF81`) e código 3 = MBRU com zeros
    (ciclo 2: SP = `0x00000081`);
  - o código `0111` aparece como `opc`, mas pela tabela do decodificador é TOS
    (ciclo 3: H = H + TOS + 1 = 1 + 2 + 1 = 4, e não 2);
  - os registradores "antes" do ciclo 3 não batem com o "depois" do ciclo 2;
  - (observado também) o cabeçalho lista 4 microinstruções, mas o
    `programa_etapa2_tarefa2.txt` tem 3; e o fim do log diz `Cycle 3` em vez de
    `Cycle 4`.
- **`saída_etapa3_tarefa1.txt`**: foi gerado com um estado inicial diferente
  dos arquivos fornecidos (mar = sp = 4, demais 0; mem[4] = 2, resto 0),
  enquanto `registradores_etapa3_tarefa1.txt` tem sp = 7, lv = 2, tos = 0x20 e
  `dados_etapa3_tarefa1.txt` tem mem = [0,0,1,2,4,8,16,32,0,…]. Com aquele
  estado inicial, a saída do simulador é idêntica ao exemplo (exceto pelo
  comprimento do último separador).
- **PDF, exemplo (6)**: `MAR = H; rd` está codificado como
  `00111000 100000000 01 0000`, com o barramento C habilitando H. O correto é
  `000000001` (MAR), que é o que o entregável usa.
- (Observação) O PDF diz que a memória de dados tem 8 linhas, mas o arquivo
  de exemplo tem 16; o simulador aceita qualquer quantidade.
