# Relatório, Trabalho 1, Threads + Semáforos

- **Disciplina:** Sistemas Operacionais
- **Autor:** Lorenzo Ficher
- **Data:** 9 de setembro de 2026
- **Repositório:** <https://github.com/lorenzoficher/so-trabalho-1-semaforos>
  (instruções de execução no `README.md`)
- **Ambiente das medições:** Windows 11, Python 3.14.3, sem WSL nem
  compilador

## 1. Descrição da aplicação

O programa implementa o problema clássico do **produtor-consumidor com
buffer circular limitado**, com múltiplos produtores e múltiplos
consumidores rodando como threads (`threading.Thread`), em torno de um
buffer compartilhado (`BoundedBuffer`, em `src/buffer.py`).

Cada produtor gera uma faixa própria e disjunta de inteiros e tenta
depositá-los no buffer, um a um. Cada consumidor retira itens do buffer e
os guarda para conferência posterior. Ao final de uma execução, o checksum
de tudo o que foi produzido é comparado ao checksum de tudo o que foi
consumido: se os dois batem, o buffer funcionou corretamente; se divergem,
algum item foi perdido, sobrescrito ou lido mais de uma vez, o que só pode
acontecer se o acesso concorrente aos índices do buffer tiver corrompido o
estado compartilhado.

Um cuidado deliberado aqui é que **a própria medição não pode ser uma
corrida**, ou não se saberia se a divergência vem do buffer ou do
instrumento. Por isso nada é somado concorrentemente. O checksum produzido
não é acumulado por ninguém: como as faixas dos produtores são disjuntas e
contíguas de 1 a 10000, ele sai de fórmula fechada, `n(n+1)/2`. Do lado do
consumo, cada consumidor acumula os valores lidos em uma lista local, e só
ao terminar os anexa a uma lista compartilhada, sob um `Lock` que existe
apenas para a instrumentação e é independente do modo em teste. A soma
final e a contagem de duplicados acontecem depois de todos os `join()`, em
uma thread só. Ou seja, qualquer divergência observada vem do
`BoundedBuffer`, nunca da forma de medir (`src/experiment.py`, e
`docs/spec/plan.md`, seção 4).

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
105,7 ms para 9,0 ms em `none`, de 299,4 ms para 91,1 ms em `counting`, e de
648,2 ms para 147,7 ms em `full`, isto é, um acréscimo de cerca de 97 ms,
208 ms e 500 ms respectivamente. O modo `full` paga mais porque, nele, o
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
| `full` | **30 / 30** | 0 / 30 | 619,2 ms | 579,3 ms | 727,4 ms |
| `counting` | 0 / 30 | **30 / 30** | 289,1 ms | 269,3 ms | 328,8 ms |
| `none` | 0 / 30 | **30 / 30** | 107,2 ms | 99,3 ms | 118,3 ms |

Detalhamento da divergência sobre as 30 execuções de cada modo. A coluna
`diferenca` do CSV é o checksum consumido **menos** o produzido, e tem
sinal: nas 30 execuções de `counting`, 16 foram negativas e 14 positivas;
nas de `none`, 4 negativas e 26 positivas. Uma diferença negativa significa
que a sobrescrita de slots predominou (itens perdidos), e uma positiva que
a leitura duplicada predominou (itens contados mais de uma vez). Como as
duas direções se cancelariam em uma média com sinal, as colunas abaixo
usam o **valor absoluto** da diferença:

| Modo | \|diferença\| média | \|diferença\| mínima | \|diferença\| máxima | Leituras duplicadas (média) |
|:--|--:|--:|--:|--:|
| `full` | 0 | 0 | 0 | 0 |
| `counting` | 194.327 | 3.443 | 586.258 | 2.888,4 |
| `none` | 1.375.302 | 9.484 | 4.041.301 | 3.606,8 |

A leitura de slot "nunca escrito" (`nao_escritos`) é raríssima nestes
parâmetros, mas não impossível: das 90 execuções da bateria, exatamente uma
a registrou, a repetição 17 do modo `counting`, com uma única leitura desse
tipo (linha `counting,17` do CSV). Nas outras 89, incluindo todas as 30 de
`none` e as 30 de `full`, ela não ocorreu. Isso mostra que a corrupção nos
modos sem exclusão mútua é *predominantemente*, mas não exclusivamente, de
índices colidindo (sobrescrita e leitura duplicada): em uma execução, o
índice de leitura chegou a apontar para um slot que nenhum produtor havia
escrito ainda. Como os dois índices sofrem perda de atualização de forma
independente, o de leitura pode, ocasionalmente, ficar à frente do de
escrita, e é exatamente isso que essa execução capturou. O modo `full`
elimina também esse caso.

### Custo da exclusão mútua

- `full` levou **5,77 vezes** mais tempo que `none` (nenhuma sincronização).
- `full` levou **2,14 vezes** mais tempo que `counting` (capacidade
  garantida, mas sem exclusão mútua).
- `counting` levou **2,70 vezes** mais tempo que `none`, evidenciando que
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
onde ocorre dentro da seção crítica. Repetindo a medição sem essa
instrumentação, nesta mesma máquina (medida auxiliar, 10 execuções por modo,
não as 30 da bateria oficial), os fatores mudam nos dois sentidos: `full`
passa a custar cerca de **16 vezes** o tempo de `none`, em vez de 5,77, mas
apenas cerca de **1,6 vezes** o de `counting`, em vez de 2,14. Ou seja, a
tabela acima *subestima* o custo do `mutex` em relação a não sincronizar
nada, e ao mesmo tempo o *superestima* em relação a só garantir capacidade.
O que se sustenta em qualquer das duas medições é a ordem, `none` <
`counting` < `full`, e a conclusão sobre corretude, que não depende de
tempo.

## 4. Por que três condições, e não duas

Bastaria comparar `none` contra `full` para responder ao pedido mínimo do
enunciado. A terceira condição, `counting`, existe para isolar a causa da
divergência. Sob `none`, uma divergência de checksum tem duas explicações
possíveis ao mesmo tempo: os índices podem ter entrado em corrida, ou o
buffer pode ter simplesmente sido usado além da sua capacidade, sem nada
para impedir isso, um problema de capacidade, não de exclusão mútua.

O modo `counting` fecha essa segunda explicação: os semáforos contadores
continuam garantindo que o número de leituras bem-sucedidas nunca ultrapasse
o número de escritas concluídas, e que o número de itens pendentes no buffer
nunca exceda a sua capacidade. Essa garantia é estrutural, vem da própria
semântica de `acquire`/`release` sobre `empty` e `full`, e não depende de
agendamento. Mesmo assim, o checksum diverge em 100% das execuções (tabela
da seção 3). A única coisa ausente em `counting`, e presente em `full`, é o
semáforo binário `mutex`. É essa condição, e não `none` isoladamente, que
sustenta a conclusão deste trabalho.

Vale distinguir duas coisas que poderiam ser confundidas aqui. Os semáforos
contadores garantem que a *contagem* de itens pendentes respeite a
capacidade; eles não garantem que cada item ocupe um slot próprio, porque o
cálculo do índice não está protegido. É por isso que `counting` perde e
duplica itens, e é também por isso que uma das 30 execuções conseguiu ler um
slot nunca escrito (seção 3): a contagem estava correta, o *endereço*
calculado a partir dela não estava.

## 5. A corrida é real, não é criada pela instrumentação

Uma objeção legítima aos números da seção 3 é que o `sleep(0)` descrito na
seção 1 poderia estar *fabricando* a corrida, e não apenas revelando-a. Se
fosse esse o caso, a conclusão deste trabalho não valeria nada fora do
experimento.

Para responder a isso, o experimento foi repetido com o `sleep(0)`
desativado, variando o número de itens por produtor. Se a corrida fosse um
artefato da instrumentação, ela desapareceria por completo; se for real, ela
deve reaparecer sozinha à medida que o número de oportunidades de troca de
thread cresce. Resultado, 5 execuções por configuração:

| Itens por produtor | Total de itens | `none` divergentes | `counting` divergentes |
|--:|--:|--:|--:|
| 2.500 | 10.000 | 5 / 5 | 0 / 5 |
| 50.000 | 200.000 | 5 / 5 | 1 / 5 |
| 250.000 | 1.000.000 | 5 / 5 | 2 / 5 |

O modo `none` diverge sempre, mesmo sem instrumentação nenhuma, porque ali
falha também a garantia de capacidade, que não depende de agendamento. O
caso interessante é `counting`: sem o `sleep(0)` e com 10.000 itens ele
passa nas 5 execuções, mas volta a divergir por conta própria quando a
escala aumenta, e com frequência crescente (diferença de -100.712 na
execução divergente com 200.000 itens, e de -504.982 e -250.337 nas duas
divergentes com 1.000.000). Ou seja, a corrida sobre os índices existe de
fato no modo `counting`; o que a instrumentação faz é apenas torná-la
observável de forma confiável em uma escala que roda em menos de um
segundo, em vez de exigir milhões de itens e depender da sorte do
agendador.

Isso também explica por que o `sleep(0)` foi mantido na bateria oficial:
sem ele, com os parâmetros padrão, o modo `counting` daria falso negativo, e
o trabalho concluiria erroneamente que semáforos contadores bastam para
garantir exclusão mútua.

## 6. Conclusão

Os resultados confirmam, de forma estatística e não apenas pontual, as duas
afirmações que o trabalho pedia para provar:

1. **Sem exclusão mútua** (modos `none` e `counting`), o acesso concorrente
   ao buffer produz resultado numérico inconsistente em **100% das 30
   execuções** de cada modo, mesmo quando a capacidade do buffer já está
   corretamente controlada por semáforos contadores (`counting`).
2. **Com exclusão mútua** garantida por um semáforo binário (modo `full`),
   o mesmo programa produz resultado numérico correto em **100% das 30
   execuções**, ao custo medido de cerca de **2,1 vezes** o tempo do modo
   `counting` e **5,8 vezes** o tempo do modo `none`.

A correção tem um custo real e mensurável, mas é a única das três condições
que garante corretude em todas as execuções observadas.
