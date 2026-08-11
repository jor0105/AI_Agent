---
name: brainstorming
description: >
  Use quando o usuário ainda quer explorar antes de decidir. Ative com "não sei
  por onde começar", "me ajuda a pensar", "quais são as opções?", "estou em
  dúvida entre X e Y", "isso faz sentido?", "como eu estruturaria isso?" ou
  quando há objetivo, mas não solução escolhida. Ajuda a reduzir incerteza e
  chegar a uma direção executável. Não use quando o usuário já pediu implementar,
  validar, escrever um plano fechado ou seguir um workflow específico como
  OpenSpec ou revisão de security.
---

# Brainstorming

## Por que brainstorm falha

O erro mais comum é pular cedo demais para alternativas: o agent lista opções
sem entender exatamente o objetivo do usuário, e o usuário recebe variedade em
vez de clareza. O segundo erro é o oposto: fazer perguntas indefinidamente sem
um critério explícito de "agora eu já entendi o bastante para recomendar".

Brainstorm correto tem três fases:

1. **Descobrir** o que realmente está sendo decidido
2. **Validar prontidão** com checks objetivos
3. **Recomendar** pelo menos 5 alternativas viáveis com trade-offs honestos

---

## Gate de prontidão

Antes de apresentar alternativas, o agent precisa provar que os 5 checks abaixo
estão fechados. Se um check estiver aberto, continue perguntando.

1. **Objetivo claro**
   O agent consegue resumir em uma frase o que o usuário quer resolver?

2. **Resultado de sucesso claro**
   O agent sabe como o usuário reconhecerá que a decisão foi boa?

3. **Restrições e contexto claros**
   O agent entende limites relevantes de prazo, stack, custo, escala, time,
   legado, risco ou experiência esperada?

4. **Critérios de decisão claros**
   O agent sabe o que pesa mais para o usuário: velocidade, simplicidade,
   controle, custo, UX, escalabilidade, segurança, manutenção ou outro critério?

5. **Espaço de solução claro**
   O agent consegue defender pelo menos 5 alternativas viáveis e genuinamente
   distintas sem inventar fatos relevantes?

Um check só fecha com evidência concreta do prompt, do contexto local ou das
respostas do usuário. Não feche check por intuição.

---

## Regras de perguntas

**Pergunte até fechar os checks, não até cumprir um formato.** O número de
perguntas não é fixo por resposta. O agent pode fazer quantas perguntas forem
necessárias ao longo da conversa.

**Existe um piso, não um teto.** Antes de apresentar as alternativas finais, o
agent deve ter feito no mínimo 5 perguntas substantivas ao longo da sessão de
brainstorming. Se 3 perguntas já parecerem suficientes, use as demais para
validar prioridades, restrições ou critérios de decisão ainda frágeis.

**Sem pergunta filler.** Nenhuma pergunta existe só para "bater meta". Toda
pergunta precisa reduzir forks reais de implementação ou de decisão.

**Perguntas revelam consequências.** Prefira perguntas que exponham o impacto
de cada escolha. "Você quer autenticação social?" é fraca. "Social ou
email/senha? Social acelera o lançamento, mas reduz controle sobre recuperação
de conta" é forte.

**Agrupe perguntas de forma humana.** Se 3 perguntas fecham os riscos principais
agora, não despeje 10 de uma vez. Pergunte em blocos que o usuário consiga
responder bem, depois recalcule os checks.

**Use a referência como suporte, não como contrato.** `references/dynamic-questioning.md`
existe para enriquecer a qualidade das perguntas e trazer bancos por domínio.
O contrato canônico desta skill está neste `SKILL.md`.

---

## Regras de alternativas

Quando os 5 checks estiverem fechados, entregue **no mínimo 5 alternativas**.
Não entregue menos de 5.

As alternativas precisam ser:

- Genuinamente distintas, não variações cosméticas do mesmo caminho
- Viáveis no contexto atual do usuário
- Comparáveis pelos mesmos critérios
- Suficientemente concretas para apoiar decisão real

Se você não consegue chegar a 5 alternativas honestas, ainda não entendeu bem o
problema ou o pedido não precisa de brainstorming. Nesses casos:

- continue perguntando para expandir o espaço de solução, ou
- conclua que o pedido já está pronto para implementação direta

Evite passar de 7 alternativas sem motivo material. Mais do que isso costuma
reduzir clareza em vez de aumentá-la.

---

## Contrato de saída

### Enquanto houver checks abertos

1. `Problema central:` uma frase sobre o que está sendo decidido
2. `Checks de prontidão:` os 5 checks com status `[x]` ou `[ ]` e evidência curta
3. `Perguntas abertas:` apenas as perguntas necessárias para fechar os checks abertos
4. `Próximo passo:` pedir as respostas do usuário

### Quando todos os checks estiverem fechados

1. `Problema central:` uma frase sobre o que está sendo decidido
2. `Checks de prontidão:` os 5 checks marcados como fechados, com evidência curta
3. `Alternativas:` no mínimo 5 alternativas numeradas

Cada alternativa deve conter:

- `Prós`
- `Contras`
- `Risco de escalabilidade`
- `Melhor ajuste`

4. `Matriz de trade-offs:` as mesmas alternativas cruzadas pelos mesmos 2 eixos
5. `Recomendação:` uma opção explícita com justificativa ancorada no contexto
6. `Próximo passo:` a decisão ou ação que falta para seguir

Não use "depende" como conclusão. Escolha uma recomendação e explique por quê.

---

## Procedimento

1. **Reconhecer o problema central.**
   Resuma em uma frase o que está sendo decidido, não apenas o que foi pedido.
   Se você não consegue fazer isso, ainda não entendeu o problema.

2. **Classificar o contexto.**
   Greenfield, Feature Addition, Refactor ou Debug. Essa classificação ajuda a
   escolher perguntas melhores e a identificar riscos reais.

3. **Preencher os checks com evidência atual.**
   Marque o que já está claro a partir do prompt, do repo, do `AGENTS.md` ou do
   histórico da conversa. Deixe aberto o que ainda depende do usuário.

4. **Perguntar até fechar os checks.**
   Faça perguntas direcionadas aos checks abertos. Antes de apresentar
   alternativas finais, garanta que a sessão já acumulou pelo menos 5 perguntas
   substantivas.

5. **Recalcular o gate após cada resposta.**
   Não presuma que uma resposta resolveu tudo. Atualize os checks e veja o que
   ainda continua em aberto.

6. **Gerar o espaço de solução.**
   Quando os 5 checks estiverem fechados, gere no mínimo 5 alternativas
   distintas. Se elas parecerem repetitivas, você ainda está cedo demais.

7. **Avaliar contra o contexto do produto.**
   Consulte `AGENTS.md` ou equivalente para restrições, métricas e viés de
   produto. A recomendação precisa ser explicada com base nesse contexto, não em
   preferência técnica abstrata.

8. **Fechar com recomendação e próximo passo.**
   Diga qual alternativa recomenda, por quê, e qual decisão ou ação destrava o
   próximo passo.

---

## Exemplos

### Caso positivo — fase de descoberta

**Entrada:** "Quero melhorar o sistema de agentes, mas ainda não sei por onde começar."

**Saída esperada:** O agent resume o problema central, mostra os 5 checks com o
que já sabe e o que ainda falta, faz perguntas dirigidas para fechar os gaps e
não apresenta alternativas finais antes de acumular evidência suficiente.

### Caso positivo — fase de alternativas

**Entrada:** "Já sei que quero reduzir latência do chat, manter custo previsível,
evitar infra muito complexa e aceitar no máximo 2s de atraso perceptível."

**Saída esperada:** O agent mostra os 5 checks fechados, apresenta pelo menos 5
alternativas comparáveis, constrói uma matriz de trade-offs e recomenda uma
delas com base no contexto.

### Caso negativo

**Entrada:** "Cria um endpoint REST para listar conversas."

**Por quê não:** O caminho já está claro. Isso não precisa de ideação; precisa
de implementação ou `plan-writing`.

### Near-miss — parece brainstorm mas não é

**Entrada:** "Quais são as melhores práticas de autenticação JWT?"

**Por quê não:** É uma pergunta de referência técnica, não uma decisão de
abordagem com contexto de produto. Responda diretamente com conhecimento
técnico.

---

## Evals de trigger

Deve acionar:

- "não sei por onde começar com o sistema de notificações"
- "quero explorar abordagens antes de decidir"
- "me ajuda a pensar entre usar Redis ou filas para isso"
- "tô em dúvida se vale a pena refatorar agora ou depois do lançamento"
- "quais são as opções pra cache aqui?"
- pedido vago como "melhora o sistema de agentes" sem especificação de como

Não deve acionar:

- "implementa o endpoint de criação de workspace" (caminho claro, sem ambiguidade)
- "quais são as melhores práticas de CORS?" (pergunta técnica de referência)
- "gera o plano de execução para essa feature" (já passou da fase de ideação)
- "explica como funciona o Zustand" (pergunta educacional, não decisão de abordagem)

---

## Evals de workflow

Para cada sessão de brainstorm concluída, as assertions abaixo devem ser verdadeiras:

- [ ] Output explicita os 5 checks de prontidão
- [ ] Nenhuma alternativa final é apresentada antes de todos os 5 checks estarem fechados
- [ ] A sessão faz no mínimo 5 perguntas substantivas antes das alternativas finais
- [ ] Cada pergunta fecha ou reduz um check aberto, um risco ou um fork real de decisão
- [ ] O output final contém no mínimo 5 alternativas numeradas
- [ ] Cada alternativa tem `Prós`, `Contras`, `Risco de escalabilidade` e `Melhor ajuste`
- [ ] O output final contém uma matriz com os mesmos 2 eixos para as alternativas
- [ ] O output final contém uma recomendação explícita com justificativa, não "depende"
- [ ] O fechamento referencia contexto real do produto, do usuário ou do sistema
- [ ] O output termina com um próximo passo claro
- [ ] Nenhum placeholder fica em aberto no output final
