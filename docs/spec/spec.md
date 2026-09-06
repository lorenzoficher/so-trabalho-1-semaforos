# Spec, Produtor-Consumidor com Semáforos

Deriva de `PRD.md`. Descreve o comportamento funcional esperado, sem entrar
em detalhes de implementação (isso fica em `plan.md`).

## 1. Glossário

| Termo | Significado |
|---|---|
| Produtor | Thread que gera um item e tenta depositá-lo no buffer. |
| Consumidor | Thread que retira um item do buffer e o soma em um total. |
| Buffer | Vetor circular de tamanho fixo, compartilhado por todas as threads. |
| Slot | Uma posição do buffer. |
| Índice de escrita | Próxima posição do buffer em que um produtor deve escrever. |
| Índice de leitura | Próxima posição do buffer de onde um consumidor deve ler. |
| Modo de sincronização | Qual conjunto de semáforos está ativo em uma execução: `none`, `counting` ou `full`. |
| Checksum produzido | Soma de todos os valores que os produtores tentaram inserir. |
| Checksum consumido | Soma de todos os valores efetivamente lidos pelos consumidores. |
| Divergência | Diferença entre checksum produzido e checksum consumido. |

## 2. Atores

- **N produtores**, cada um gera uma faixa própria e disjunta de inteiros
  positivos (para que o checksum produzido total seja sempre calculável de
  forma independente da ordem de execução).
- **N consumidores**, cada um consome uma quantidade fixa de itens.

## 3. Os três modos de sincronização

### 3.1. `none`, nenhuma sincronização

- Produtores escrevem no buffer sem esperar por espaço livre.
- Consumidores leem do buffer sem esperar por item disponível.
- Nenhum mecanismo protege o incremento dos índices de leitura e escrita.
- Comportamento esperado: itens são sobrescritos antes de serem consumidos,
  e/ou lidos antes de serem escritos (slot ainda vazio), e/ou lidos mais de
  uma vez. O checksum consumido diverge do produzido em praticamente toda
  execução.

### 3.2. `counting`, semáforos contadores sem exclusão mútua

- Dois semáforos contadores, `empty` (inicializado com a capacidade do
  buffer) e `full` (inicializado em zero), controlam quando um produtor pode
  escrever e quando um consumidor pode ler. Isso garante que a quantidade
  total de operações de escrita bem-sucedidas seja igual à quantidade total
  de operações de leitura bem-sucedidas, sempre igual ao número total de
  itens.
- Não existe semáforo binário protegendo o cálculo do índice de escrita, do
  índice de leitura, nem o acesso ao slot.
- Comportamento esperado: como o incremento dos índices não é atômico, dois
  produtores podem calcular o mesmo índice de escrita (um sobrescreve o
  outro) e dois consumidores podem calcular o mesmo índice de leitura (um lê
  o mesmo valor duas vezes). A quantidade de operações continua batendo, mas
  os valores lidos divergem dos valores escritos. O checksum consumido
  diverge do produzido em praticamente toda execução, isolando a exclusão
  mútua (e não a capacidade do buffer) como a causa.

### 3.3. `full`, semáforos contadores mais semáforo binário

- Os mesmos `empty`/`full` de `counting`, mais um semáforo binário `mutex`
  (inicializado em 1), que protege o trecho onde o índice é lido, calculado,
  usado para acessar o slot, e incrementado.
- Comportamento esperado: checksum consumido sempre igual ao checksum
  produzido, em toda execução.

## 4. Entradas e saídas do programa principal

**Entrada** (linha de comando): modo de sincronização. Número de produtores,
consumidores, itens por produtor e capacidade do buffer têm valor padrão
fixo, para manter as três condições comparáveis (RNF2 do PRD), mas podem ser
sobrescritos explicitamente para fins de exploração.

**Saída**: uma linha por execução, com o modo, o checksum produzido, o
checksum consumido, a diferença, a contagem de leituras duplicadas, a
contagem de leituras de slots ainda não escritos, e o tempo decorrido em
milissegundos.

## 5. Bateria de execuções

Um script separado roda o programa principal várias vezes (parâmetro
configurável, padrão 30) para cada um dos três modos, e agrega:

- quantas execuções tiveram diferença zero (corretas) e quantas divergiram,
  por modo;
- tempo médio, mínimo e máximo por modo;
- grava todas as execuções individuais em `results/battery_results.csv`.

## 6. Testes automatizados

Testes de API do buffer, sem concorrência real (uma thread só, chamadas que
nunca bloqueiam), cobrindo:

- inserir e retirar um item preserva o valor;
- a ordem de retirada é a ordem de inserção (FIFO);
- o buffer reaproveita os slots corretamente ao dar a volta (índice módulo
  capacidade);
- os três modos aceitam a mesma API (`put`/`get`) sem lançar exceção quando
  usados dentro da própria capacidade, em uma thread só.

Esses testes não provam nem derrubam a hipótese de exclusão mútua, eles
provam que a estrutura de dados em si está correta. A prova de exclusão
mútua é estatística e vem da bateria de execuções (seção 5), não dos testes
unitários. Essa separação está registrada em
`docs/adr/0002-tres-condicoes-experimentais.md`.
