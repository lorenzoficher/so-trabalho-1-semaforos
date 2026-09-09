# Relatório, Trabalho 1, Threads + Semáforos

- **Disciplina:** Sistemas Operacionais
- **Autor:** Lorenzo Ficher
- **Repositório:** ver `README.md` para instruções de execução

## 1. Descrição da aplicação

O programa implementa o problema clássico do **produtor-consumidor com
buffer circular limitado**, com múltiplos produtores e múltiplos
consumidores rodando como threads (`threading.Thread`), em torno de um
buffer compartilhado (`BoundedBuffer`, em `src/buffer.py`).

Cada produtor gera uma faixa própria e disjunta de inteiros e tenta
depositá-los no buffer, um a um. Cada consumidor retira itens do buffer e
os acumula em uma soma de verificação (checksum). Ao final de uma execução,
o checksum de tudo o que foi produzido é comparado ao checksum de tudo o
que foi consumido: se os dois batem, o buffer funcionou corretamente; se
divergem, algum item foi perdido, sobrescrito ou lido mais de uma vez, o
que só pode acontecer se o acesso concorrente aos índices do buffer tiver
corrompido o estado compartilhado.

O programa aceita três **modos de sincronização**, escolhidos por
parâmetro, sem nenhuma outra mudança de código entre eles:

- **`none`**, nenhum semáforo. Produtores escrevem e consumidores leem sem
  esperar por nada.
- **`counting`**, dois semáforos contadores (`empty`, `full`) controlam a
  capacidade do buffer (produtor espera se estiver cheio, consumidor espera
  se estiver vazio), mas nada protege o cálculo dos índices de leitura e
  escrita.
- **`full`**, os mesmos semáforos contadores mais um semáforo binário
  (`mutex`) que protege o trecho onde o índice é lido, calculado, usado
  para acessar o slot do buffer, e incrementado.

A escolha desse problema, entre as sugestões do enunciado, foi deliberada: é
o único, entre os sugeridos, em que o semáforo é necessário por dois
motivos ao mesmo tempo, contar recursos disponíveis (`empty`/`full`) e
excluir mutuamente (`mutex`), e não apenas como substituto de um `Lock`
comum. O raciocínio completo está em `PRD.md`, seção 2.

O motivo da divergência é sempre o mesmo trecho de código, em
`src/buffer.py`: `indice = _write_index % capacidade` seguido, mais tarde,
de `_write_index += 1`, não é uma operação atômica. Entre a leitura do
índice e a sua gravação de volta, o interpretador pode trocar de thread. Se
isso acontecer, duas threads produtoras podem calcular o mesmo índice de
escrita (uma sobrescreve a outra), ou duas consumidoras podem calcular o
mesmo índice de leitura (uma lê o mesmo valor duas vezes). O modo `full`
elimina exatamente essa possibilidade, protegendo esse trecho com o
semáforo binário `mutex`.

Como a janela dessa corrida é, por natureza, curta, o código insere um
`time.sleep(0)` (que apenas cede o processador para outra thread pronta,
sem de fato dormir) entre a leitura do índice e sua gravação, para tornar a
divergência observável de forma confiável em qualquer máquina, em vez de
depender da sorte do agendador do sistema operacional. A chamada está
presente nos três modos, mas o seu custo **não** é igual entre eles: medido
nesta máquina em 10 execuções por modo, removê-la faz o tempo médio cair de
85,3 ms para 6,6 ms em `none`, de 244,2 ms para 76,3 ms em `counting`, e de
484,1 ms para 106,5 ms em `full`, isto é, um acréscimo de cerca de 79 ms,
168 ms e 378 ms respectivamente. O modo `full` paga mais porque, nele, o
`sleep(0)` acontece **com o `mutex` já adquirido**: cada cessão de
processador ocorre dentro da seção crítica e serializa as demais threads. A
consequência para a leitura dos números da seção 3 está registrada ali, na
subseção "Custo da exclusão mútua". A escolha de instrumentar assim é
discutida em `docs/adr/0001-escolha-da-linguagem-python.md`.

## 2. Testes implementados

### 2.1. Testes determinísticos da API (`tests/test_buffer.py`)

Executados com `pytest`, em uma thread só, sem depender de tempo ou
agendamento. Cobrem, para os três modos: inserir e retirar um item preserva
o valor; a ordem de retirada é a ordem de inserção (FIFO); o buffer
reaproveita corretamente os slots ao dar a volta (índice módulo
capacidade); e uma capacidade inválida levanta erro. Esses testes provam
que a estrutura de dados em si está correta, isolando esse fator do
fenômeno de concorrência, que é medido separadamente (seção 2.3).

Resultado: **10 testes, 10 aprovados**, em todas as execuções.

### 2.2. Testes de validação de entrada (`tests/test_experiment.py`)

Também determinísticos e sem concorrência, cobrem os erros que
`run_experiment` deve recusar *antes* de criar qualquer thread: número de
produtores ou de consumidores inválido (zero ou negativo), e total de itens
não divisível pelo número de consumidores, caso em que a divisão de trabalho
entre consumidores não fecharia e a execução travaria esperando itens que
nunca chegam. São 4 testes, todos aprovados.

Somados aos da seção 2.1, a suíte tem **14 testes, 14 aprovados**
(`python -m pytest tests/ -v`).

### 2.3. Bateria de execuções (`tests/battery.py`)

Roda o experimento completo (4 produtores, 4 consumidores, 2500 itens por
produtor, 10000 itens no total, buffer de 10 slots) **30 vezes para cada um
dos três modos**, e registra cada execução individual em
`results/battery_results.csv`. O veredito é assimétrico entre condições, e
foi definido antes de rodar a bateria (`PRD.md`, seção 6, critérios CA1 a
CA3): espera-se **zero divergências em todas as 30 execuções** do modo
`full` (é uma invariante que deve sempre se sustentar), e **divergência em
quase todas as 30 execuções** dos modos `none` e `counting` (uma corrida de
dados não se comprova com uma execução só, é preciso ver que ela se repete).

## 3. Execução do experimento e resultados

Bateria executada nesta máquina (Windows 11, Python 3.14.3, sem WSL nem
compilador), com os parâmetros padrão (30 repetições por modo). Os números
abaixo vêm exatamente de `results/battery_results.csv`, sem estimativa.

| Modo | Execuções corretas | Execuções divergentes | Tempo médio | Tempo mínimo | Tempo máximo |
|:--|--:|--:|--:|--:|--:|
| `full` | **30 / 30** | 0 / 30 | 430,9 ms | 417,7 ms | 459,9 ms |
| `counting` | 0 / 30 | **30 / 30** | 265,5 ms | 208,8 ms | 583,0 ms |
| `none` | 0 / 30 | **30 / 30** | 85,0 ms | 77,0 ms | 96,7 ms |

Detalhamento da divergência sobre as 30 execuções de cada modo. A coluna
`diferenca` do CSV é o checksum consumido **menos** o produzido, e tem
sinal: nas 30 execuções de `counting`, 19 foram negativas e 11 positivas;
nas de `none`, 3 negativas e 27 positivas. Uma diferença negativa significa
que a sobrescrita de slots predominou (itens perdidos), e uma positiva que
a leitura duplicada predominou (itens contados mais de uma vez). Como as
duas direções se cancelariam em uma média com sinal, as colunas abaixo
usam o **valor absoluto** da diferença:

| Modo | \|diferença\| média | \|diferença\| mínima | \|diferença\| máxima | Leituras duplicadas (média) |
|:--|--:|--:|--:|--:|
| `full` | 0 | 0 | 0 | 0 |
| `counting` | 161.554 | 5.371 | 339.769 | 2.792,6 |
| `none` | 1.493.564 | 2.156 | 8.214.967 | 3.620,3 |

Nenhuma execução teve leitura de slot "nunca escrito" (`nao_escritos`), nos
três modos, porque nenhum consumidor conseguiu ultrapassar o número de
itens realmente inseridos até aquele ponto por tempo suficiente para isso;
a corrupção observada é inteiramente de índices colidindo (sobrescrita e
leitura duplicada), não de leitura adiantada.

### Custo da exclusão mútua

- `full` levou **5,07 vezes** mais tempo que `none` (nenhuma sincronização).
- `full` levou **1,62 vezes** mais tempo que `counting` (capacidade
  garantida, mas sem exclusão mútua).
- `counting` levou **3,12 vezes** mais tempo que `none`, evidenciando que
  boa parte do custo de `full` sobre `counting` já vem de garantir a
  capacidade do buffer, e não só do `mutex` adicional.

Os tempos absolutos variam de execução para execução desta bateria para a
outra (dependem da carga do resto do sistema operacional no momento, este
não é um ambiente isolado de benchmark), mas a ordem relativa entre os três
modos e a conclusão sobre corretude se mantiveram estáveis em todas as
baterias rodadas para este trabalho.

Uma ressalva importante sobre esses três fatores: eles medem o programa
**instrumentado**, não o custo intrínseco de um mutex. Como a seção 1
detalha, o `sleep(0)` inserido para tornar a corrida observável é cobrado de
forma desigual entre os modos, e é cobrado mais caro justamente em `full`,
onde ocorre dentro da seção crítica. Sem essa instrumentação, e nesta mesma
máquina, `full` custa cerca de **16 vezes** o tempo de `none`, em vez de
5,07 vezes, e cerca de **1,4 vezes** o de `counting`, em vez de 1,62 (medida
auxiliar, 10 execuções por modo, não as 30 da bateria oficial). Ou seja, o
fator relatado na tabela acima *subestima* o custo relativo da exclusão
mútua, não o exagera. O que se sustenta em qualquer das duas medições é a
ordem, `none` < `counting` < `full`, e a conclusão sobre corretude, que não
depende de tempo.

## 4. Por que três condições, e não duas

Bastaria comparar `none` contra `full` para responder ao pedido mínimo do
enunciado. A terceira condição, `counting`, existe para isolar a causa da
divergência. Sob `none`, uma divergência de checksum tem duas explicações
possíveis ao mesmo tempo: os índices podem ter entrado em corrida, ou o
buffer pode ter simplesmente sido usado além da sua capacidade, sem nada
para impedir isso, um problema de capacidade, não de exclusão mútua.

O modo `counting` fecha essa segunda explicação: os semáforos contadores
continuam garantindo que o número de escritas bem-sucedidas seja sempre
igual ao número de leituras bem-sucedidas (nenhuma execução registrou
`nao_escritos` maior que zero), a capacidade nunca é violada, e mesmo assim
o checksum diverge em 100% das execuções (tabela da seção 3). A única coisa
ausente em `counting`, e presente em `full`, é o semáforo binário `mutex`.
É essa condição, e não `none` isoladamente, que sustenta a conclusão deste
trabalho.

## 5. Conclusão

Os resultados confirmam, de forma estatística e não apenas pontual, as duas
afirmações que o trabalho pedia para provar:

1. **Sem exclusão mútua** (modos `none` e `counting`), o acesso concorrente
   ao buffer produz resultado numérico inconsistente em **100% das 30
   execuções** de cada modo, mesmo quando a capacidade do buffer já está
   corretamente controlada por semáforos contadores (`counting`).
2. **Com exclusão mútua** garantida por um semáforo binário (modo `full`),
   o mesmo programa produz resultado numérico correto em **100% das 30
   execuções**, ao custo medido de cerca de **1,6 vezes** o tempo do modo
   `counting` e **5 vezes** o tempo do modo `none`.

A correção tem um custo real e mensurável, mas é a única das três condições
que garante corretude em todas as execuções observadas.
