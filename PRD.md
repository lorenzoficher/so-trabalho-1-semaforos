# PRD, Produtor-Consumidor com Semáforos POSIX (via `threading` em Python)

- **Disciplina:** Sistemas Operacionais
- **Trabalho:** Trabalho 1, Threads + Semáforos
- **Autor:** Lorenzo Ficher
- **Status:** Aprovado para implementação

## 1. Objetivo

Implementar um programa concorrente que use threads e semáforos, e provar,
experimentalmente, duas coisas:

1. Sem nenhum mecanismo de exclusão mútua, o acesso concorrente a um recurso
   compartilhado produz resultados numéricos inconsistentes.
2. Com semáforos usados corretamente (contagem de recursos e exclusão mútua),
   o mesmo programa passa a produzir sempre o resultado correto.

O enunciado do trabalho está reproduzido em `docs/Enunciado.md`.

## 2. Problema escolhido

**Produtor-consumidor com buffer circular limitado**, com múltiplos produtores
e múltiplos consumidores.

Motivo da escolha, entre as sugestões do enunciado (produtores/consumidores,
jantar dos filósofos, Pix, restaurante universitário, controle de estoque):
este é o problema em que os semáforos são a primitiva certa por dois motivos
ao mesmo tempo, não só um. O semáforo contador modela a capacidade do buffer
(quantos slots livres, quantos itens disponíveis), algo que um `Lock` comum
não expressa. E o semáforo binário protege a seção crítica dos índices. Um
problema baseado só em saldo (Pix, estoque) usaria semáforo apenas como mutex,
o que o próprio enunciado pede para evitar ("procure problemas cuja
viabilidade de corretude ocorra através de semáforos").

## 3. Requisitos funcionais

- RF1: o programa deve criar múltiplas threads produtoras e múltiplas threads
  consumidoras, usando `threading.Thread`.
- RF2: deve existir um buffer circular de capacidade fixa, compartilhado por
  todas as threads.
- RF3: o programa deve suportar três modos de sincronização, selecionáveis
  por parâmetro, sem alterar o restante da lógica:
  - `none`, nenhuma sincronização.
  - `counting`, semáforos contadores de capacidade (`empty`, `full`), sem
    exclusão mútua sobre os índices.
  - `full`, semáforos contadores mais um semáforo binário (`mutex`) sobre os
    índices e o acesso aos slots.
- RF4: cada execução deve calcular uma soma de verificação (checksum) dos
  itens produzidos e uma soma de verificação dos itens consumidos, e comparar
  as duas.
- RF5: cada execução deve medir e reportar o tempo de execução.
- RF6: deve existir uma bateria de execuções (várias repetições por modo) que
  agregue os resultados em uma tabela.
- RF7: deve existir um conjunto de testes automatizados que exercite a API do
  buffer de forma determinística, sem depender de concorrência real.

## 4. Requisitos não funcionais

- RNF1: o código deve rodar em Windows sem depender de WSL, compilador C ou
  JDK, usando apenas Python 3 e a biblioteca padrão (mais `pytest` para os
  testes).
- RNF2: os únicos parâmetros que variam entre as três condições
  experimentais são os relacionados à sincronização. Número de produtores,
  consumidores, itens e capacidade do buffer permanecem fixos entre
  condições, para permitir comparação.
- RNF3: o experimento deve ser determinístico o suficiente para reproduzir a
  divergência de checksum de forma confiável nos modos `none` e `counting`,
  e a ausência de divergência no modo `full`, em qualquer máquina Windows com
  Python 3.10+.

## 5. Fora de escopo

- Interface gráfica.
- Persistência dos itens em disco ou banco de dados.
- Execução distribuída em mais de um processo ou máquina.
- Suporte a outras linguagens além de Python nesta entrega (a decisão está
  registrada em `docs/adr/0001-escolha-da-linguagem-python.md`).

## 6. Critérios de aceitação

- CA1: rodar o experimento no modo `full` N vezes seguidas resulta em zero
  divergências de checksum em todas as execuções.
- CA2: rodar o experimento no modo `none` N vezes seguidas resulta em
  divergência de checksum em praticamente todas as execuções.
- CA3: rodar o experimento no modo `counting` N vezes seguidas resulta em
  divergência de checksum em praticamente todas as execuções, isolando a
  exclusão mútua como a variável responsável (a capacidade do buffer já está
  garantida nesse modo).
- CA4: os testes automatizados da API do buffer passam de forma
  determinística, sem depender de tempo ou agendamento de threads.
- CA5: o relatório final (`docs/relatorio.md`) documenta o experimento, os
  resultados numéricos obtidos de fato (não estimados) e a conclusão.

## 7. Metodologia de desenvolvimento

Este trabalho segue um fluxo do tipo SDD (spec-driven development):

1. Este PRD define o problema e os critérios de aceitação.
2. `docs/spec/spec.md` detalha o comportamento funcional esperado.
3. `docs/spec/plan.md` detalha a arquitetura técnica e as decisões de
   projeto (com ADRs em `docs/adr/`).
4. `docs/spec/tasks.md` quebra o plano em tarefas.
5. Cada tarefa vira uma issue em `docs/issues/`, com critério de aceite
   próprio, rastreável até este PRD.
6. O código em `src/` e os testes em `tests/` implementam as issues.
7. `docs/relatorio.md` fecha o ciclo com os resultados observados.

## 8. Referências

- Enunciado do trabalho: `docs/Enunciado.md`.
- Repositório usado como referência metodológica (problema similar, projeto
  de terceiro, não reutilizado como código):
  `https://github.com/PPrauchner/SO-Trabalho-1-Semaforos/tree/dev`.
