# ADR 0001, Python com `threading.Semaphore`, em vez de Java ou C

## Contexto

O enunciado sugere Java (`Runnable`/`Thread` e a classe `Semaphore`). Esta
máquina não tem JDK instalado, apenas um JRE 8 (sem `javac`), e não tem WSL
com uma distribuição Linux configurada nem `gcc`, o que descarta C com
`pthreads` e semáforos POSIX sem instalar ferramentas adicionais. Python 3.14
e `pytest` já estão instalados e funcionam nativamente no Windows.

Uma preocupação real com Python é o GIL (Global Interpreter Lock): como só
uma thread executa bytecode Python por vez, é razoável perguntar se uma
condição de corrida chega a se manifestar de verdade, ou se o GIL a esconde.

## Decisão

Usar Python 3 com `threading.Thread` e `threading.Semaphore`.

A resposta para a preocupação do GIL é que ele não torna atômicas operações
de leitura, cálculo e escrita que ocupam mais de um bytecode, como
`indice += 1`. O GIL pode ser liberado entre esses passos, para qualquer
outra thread pronta para rodar. Na prática, porém, a primeira tentativa foi
reduzir o intervalo de troca do interpretador
(`sys.setswitchinterval()`, padrão 5 milissegundos) para uma fração de
microssegundo, e essa tentativa não bastou: em execuções de teste, o modo
`counting` não divergiu nenhuma vez em cerca de dez execuções seguidas,
mesmo com o intervalo reduzido, porque cada chamada a `put`/`get` é curta
demais (poucos bytecodes, sem laço interno) para que o intervalo de troca,
por si só, garanta uma troca de thread bem no meio da seção crítica.

A solução que de fato funcionou, e que ficou no código, foi inserir um
`time.sleep(0)` (que só cede o GIL, não dorme de fato) entre a leitura do
índice e a sua gravação, dentro de `BoundedBuffer.put`/`get`
(`src/buffer.py`). Essa é uma técnica didática padrão para tornar uma janela
de corrida naturalmente estreita em uma janela observável de forma
confiável, sem mudar o que a seção crítica faz, só o quão provável é que ela
seja interrompida no meio. Como o `sleep(0)` está no mesmo caminho de código
para os três modos, ele é um custo constante presente em todas as condições
por igual, e não invalida a comparação de tempo entre elas.

`threading.Semaphore` do Python é uma primitiva real de sincronização entre
threads do sistema operacional (a CPython usa uma condition variable apoiada
em uma trava de SO), não uma simulação. `acquire()`/`release()` correspondem
diretamente a P e V.

## Alternativas consideradas

- **Java** (`java.util.concurrent.Semaphore`). Rejeitada nesta entrega por
  falta de JDK na máquina de desenvolvimento (só o JRE 8 está instalado, sem
  `javac`); teria exigido instalar um JDK antes de escrever qualquer código.
- **C com `pthreads` e semáforos POSIX (via WSL)**. Rejeitada porque o WSL
  instalado não tem uma distribuição Linux configurada (só uma imagem parada
  do Docker Desktop), e não há `gcc`/`make` no Windows; instalar e configurar
  esse ambiente teria sido trabalho de infraestrutura, não de sistemas
  operacionais.
- **C com a API nativa do Windows** (`CreateThread`, `CreateSemaphoreW`).
  Rodaria nativamente, mas troca uma API de propósito didático (POSIX,
  historicamente ligada a Dijkstra e a este tipo de exercício) por uma API
  proprietária, sem ganho conceitual para o trabalho.

## Consequências

- O projeto roda com `python` puro, sem passo de compilação e sem WSL.
- A prova de exclusão mútua depende do `time.sleep(0)` citado acima. Sem
  ele, o modo `none` ainda divergiria na maioria das execuções (o
  intervalo padrão de troca já é curto o bastante para isso, como mostrou o
  teste inicial), mas o modo `counting` se tornaria pouco confiável para
  demonstração, variando entre máquinas e versões do interpretador.
- Otimização de bytecode não é uma variável do experimento como seria em C
  compilado com `-O0`/`-O2`; não há flag de compilação equivalente em
  Python puro, então essa dimensão simplesmente não existe aqui.
