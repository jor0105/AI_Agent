## Sumário

Este arquivo apoia a fase de perguntas da skill `brainstorming`. Ele não define
o contrato principal da skill; esse contrato vive no `SKILL.md`. Use esta
referência quando precisar formular perguntas melhores para fechar os 5 checks
de prontidão ou quando o domínio técnico pedir trade-offs mais específicos.

Cobre: princípios de boas perguntas, algoritmo baseado em checks abertos, regra
de no mínimo 5 perguntas substantivas antes das alternativas finais, bancos de
perguntas por domínio e um exemplo end-to-end.

---

# Dynamic Questioning

> **PRINCIPLE:** Questions are not about gathering data. They are about
> **closing uncertainty that changes the decision**.

> A question is only useful if its answer changes the solution space, the trade-
> offs, the recommendation, or the next step.

---

## When To Open This File

Open this reference when one or more of these are true:

- one of the 5 readiness checks is still open
- the domain is technical and trade-offs are not obvious
- the user request implies multiple architecture paths
- you need help converting vague intent into concrete decision questions

Do not open this file just because the user is brainstorming. Start with the
main `SKILL.md`. Come here only when you need better question design.

---

## The 5 Readiness Checks

The main skill uses these checks. This reference exists to help close them:

1. **Objective clarity**
2. **Success clarity**
3. **Constraints and context clarity**
4. **Decision criteria clarity**
5. **Solution-space clarity**

If a question does not help close at least one of these checks, delete it.

---

## Core Principles

### 1. Questions Reveal Consequences

A weak question gathers surface preference.

```markdown
Weak: "Do you want social login?"
```

A strong question reveals what changes in the implementation.

```markdown
Strong: "Social login or email/password?

Social accelerates launch and reduces password flows.
Email/password gives more control over recovery and security policy.

Which trade-off matters more right now?"
```

### 2. Context Before Content

Before asking specifics, identify what kind of problem this is:

| Context                      | Question Focus                                             |
| ---------------------------- | ---------------------------------------------------------- |
| **Greenfield**               | Foundational decisions: stack, hosting, scale              |
| **Feature Addition**         | Integration points, legacy constraints, breaking changes   |
| **Refactor**                 | What is broken today, and what must improve                |
| **Debug**                    | Symptoms, reproduction, failure boundaries, impact         |

### 3. Minimum Useful Question

Each question should remove a path you would otherwise need to keep open.

```text
Before answer:
- Path A
- Path B
- Path C

After answer:
- Path A removed
- Path B confirmed
```

If the answer would not change your recommendation, the question is noise.

### 4. No Filler To Reach Five

The session needs **at least 5 substantive questions before final
alternatives**, but the solution is never filler.

If the first 3 questions closed the biggest gaps, use the remaining questions to
validate:

- decision priorities
- non-obvious constraints
- acceptable trade-offs
- scale assumptions
- rollout tolerance

### 5. Checks, Then Alternatives

Do not present final alternatives just because you already asked 5 questions.
The real gate is:

- at least 5 substantive questions asked across the session
- all 5 readiness checks closed

Both conditions must be true.

---

## Question Generation Algorithm

```text
INPUT: User request + known context + current readiness checks
│
├── STEP 1: Restate the decision
│   └── What is actually being decided?
│
├── STEP 2: Mark the 5 checks
│   ├── Closed with evidence
│   └── Open with missing evidence
│
├── STEP 3: Generate only questions that close open checks
│   ├── Objective questions
│   ├── Success questions
│   ├── Constraint questions
│   ├── Decision-criteria questions
│   └── Solution-space questions
│
├── STEP 4: Prioritize
│   ├── P0: Questions that change the entire direction
│   ├── P1: Questions that affect >30% of implementation
│   ├── P2: Questions that sharpen recommendation quality
│   └── P3: Nice-to-have detail; defer if not needed
│
├── STEP 5: Track session floor
│   ├── Have we asked 5 substantive questions already?
│   └── If not, keep questioning until both the floor and the checks are satisfied
│
└── STEP 6: Stop only when both are true
    ├── All 5 checks are closed
    └── At least 5 substantive questions were asked
```

---

## Question Template

Repeat this block as many times as needed. There is no fixed number per message.

```markdown
### [Question Title]

**Pergunta:** [clear question]

**Por que isso importa:**
- [decision impact]
- [implementation consequence]

**Opções com trade-offs:**
- Opção A → [upside] / [cost]
- Opção B → [upside] / [cost]
- Opção C → [if useful]

**Se não responder:**
- [default assumption and risk]
```

---

## Mapping Question Types To Checks

### 1. Objective Clarity

Ask these when the user goal is vague:

- "Qual resultado você quer melhorar de verdade?"
- "O problema é velocidade, qualidade, custo, UX ou outra coisa?"
- "Se eu resolver só uma parte disso agora, qual parte mais dói?"

### 2. Success Clarity

Ask these when the user wants "melhorar" something but no success signal exists:

- "Como você vai saber que essa decisão funcionou?"
- "Qual métrica ou efeito visível precisa melhorar?"
- "O que seria um resultado bom o bastante para esta fase?"

### 3. Constraints And Context

Ask these when the solution depends on limits:

- "Existe prazo, stack, budget ou legado que não podemos romper?"
- "Isso precisa caber na arquitetura atual ou pode exigir novo componente?"
- "Há restrição de time, operação ou manutenção que pese nessa decisão?"

### 4. Decision Criteria

Ask these when multiple good paths exist:

- "Você otimiza mais velocidade de entrega ou controle de longo prazo?"
- "Prefere solução simples agora ou base mais robusta para escalar?"
- "Entre custo, latência e simplicidade, o que pesa mais?"

### 5. Solution-Space Clarity

Ask these when you still cannot defend 5 distinct alternatives:

- "Você quer comparar abordagens técnicas, de produto, ou rollout?"
- "Aceita soluções híbridas ou quer uma escolha única?"
- "Quer priorizar MVP, escala futura ou facilidade de manutenção?"

---

## Domain-Specific Banks

Use these only if the domain matches the request.

### E-Commerce

| Question                          | Why It Matters                                                     | Trade-offs                         |
| --------------------------------- | ------------------------------------------------------------------ | ---------------------------------- |
| **Single or Multi-vendor?**       | Multi-vendor changes commissions, dashboards and payouts           | +Revenue, -Complexity              |
| **Inventory Tracking?**           | Requires stock tables, reservation logic and alerts                | +Accuracy, -Development time       |
| **Digital or Physical Products?** | Physical products bring shipping, tracking and fulfillment         | +Reach, -Ops complexity            |
| **Subscription or One-time?**     | Subscription adds recurring billing, dunning and proration         | +Revenue, -Complexity              |

### Authentication

| Question                    | Why It Matters                                       | Trade-offs                   |
| --------------------------- | ---------------------------------------------------- | ---------------------------- |
| **Social Login Needed?**    | OAuth providers vs. password recovery flows          | +UX, -Control                |
| **Role-Based Permissions?** | RBAC tables, policy enforcement and admin surfaces   | +Security, -Development time |
| **2FA Required?**           | TOTP/SMS flows, backup codes and recovery handling   | +Security, -UX friction      |
| **Email Verification?**     | Verification tokens, email service and resend logic  | +Security, -Sign-up friction |

### Real-time

| Question                       | Why It Matters                                                        | Trade-offs                        |
| ------------------------------ | --------------------------------------------------------------------- | --------------------------------- |
| **WebSocket or Polling?**      | WebSocket changes infra and scaling                                   | +Latency, -Complexity             |
| **Expected Concurrent Users?** | Determines whether single-node, Redis or specialized infra is enough  | +Scale, -Cost                     |
| **Message Persistence?**       | Changes history storage, pagination and durability                    | +UX, -Storage                     |
| **Ephemeral or Durable?**      | Durable delivery impacts write path and latency                       | +Reliability, -Latency            |

### Content/CMS

| Question                    | Why It Matters                              | Trade-offs                    |
| --------------------------- | ------------------------------------------- | ----------------------------- |
| **Rich Text or Markdown?**  | Rich text adds sanitization and editor cost | +UX, -Complexity              |
| **Draft/Publish Workflow?** | Requires status, scheduling and versioning  | +Control, -Complexity         |
| **Media Handling?**         | Changes uploads, storage and optimization   | +Features, -Development time  |
| **Multi-language?**         | Requires i18n model and translation UX      | +Reach, -Complexity           |

---

## Example

```text
USER REQUEST: "Build an Instagram clone"

CURRENT CHECKS
- Objective clarity: closed
- Success clarity: open
- Constraints/context: open
- Decision criteria: open
- Solution-space clarity: open

QUESTIONS ASKED SO FAR
- 0

NEXT QUESTIONS
1. What matters more for v1: speed to launch or long-term control?
2. Do you need instant notifications or is small delay acceptable?
3. What scale do you expect in the first months?
4. Should media handling optimize for MVP speed or lower long-term cost?
5. What does success for v1 mean: user growth, low infra cost, or polished UX?
```

After answers arrive, update the checks. If all checks close and the session has
already asked at least 5 substantive questions, then move to 5+ alternatives.

---

## Final Reminder

1. The main skill owns the contract
2. This file helps produce better questions
3. The true stop condition is not "I asked 5"
4. The true stop condition is "I asked at least 5 and all 5 checks are closed"
