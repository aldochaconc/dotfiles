---
name: writing
description: Use before writing a doc, spec, artifact, pull request body, commit body, comment or tracker item; again before it ships; to audit prose that already exists; to name a slop pattern and its repair; to log a finding other SWEs have to correct the same way.
---

# Writing

A register, two gates and a log. One cause produces every row of the register: the training
distribution is conversation and general prose, both of which reward filling an evaluative or
phatic slot that a technical report does not have. An unlisted pattern is recognized by that
cause and enters through the log.

The gates are fixed. The log grows: a row enters when a human corrects a pattern, or when the
same defect appears a second time. A recurring row is promoted to the register below, or to a
rule in the skill that owns the surface, and the log keeps the observation. The Replying
section of the instructions file states the conversational rules and points here for the
register.

## Slop register

| Slop | Form | Admissible | Repair |
|---|---|---|---|
| Explanatory subtitle | `Name: <gloss>`, a heading shaped as a question, or a field label shaped as one (`**Why.**`) | a colon separating an identifier from its content, or carrying an enumeration | the name alone. `description` carries what it is |
| Definite-article heading | `The <noun>` as a heading, reifying the content | a proper name that carries the article | the noun alone, or a heading that names the content |
| Phatic move | opener, receipt of the request, apology, closing restatement, coda grading the reply | none | the answer opens, the last fact closes |
| Epiphonema | a closing line that elevates: counterfactual, general, or a restatement | none | name the state |
| Hypercorrect enumeration | one sentence in a bullet; a causal paragraph split into bullets | three or more parallel, addressable items | prose for causality, a list for parallel items |
| Corrective antithesis | `not X but Y` with X never claimed; `rather than X, Y` | a correction of an error that was quoted or measured | Y alone |
| Reply as subject | a sentence about the message: `good point`, `that reframes it` | none | the answer |
| Address | first or second person: `you need to`, `here is your` | none | the outcome: `fixed: mapper.ts:88` |
| Process narration | `let me check the files`, `I will look into` | none | the tool calls already show it |
| Metadiscourse | `in this section`, `it is worth noting`, `as mentioned above` | a heading, an index, a stated scope | delete the signal, keep the content |
| Evaluative intensification | `robust`, `seamless`, `very`, `really`, `clearly`, exclamation marks, emoji | a domain term evaluative by definition, such as a severity level | the number, the behaviour, or silence |
| Epistemic hedging | `I think`, `it seems`, `might`, `could potentially`, with nothing behind them | an uncertainty with its basis and scope declared | `not verified: <what was not checked>` |
| Colon preamble | a fragment, a colon, and then the fact | a label before a value: `Run: npm test` | the fact as a full sentence |
| Appositive gloss | a clause after a comma restating the main clause in other words | an apposition that adds a fact | delete the clause |
| One assertion | two claims in one sentence; a consequence riding on its cause | none | one sentence per claim, each with its own subject |
| Tricolon | three parallel items inside one sentence | three or more items in a list or a table | the items leave for a list |
| Dash | the default connector between clauses; a sentence-final amplifier; an unpaired dash where a comma aposes | a paired aside; an abrupt break in quoted speech; an en dash between numerals of a range | a colon explains, a comma aposes, a period opens a new assertion |
| Clause symmetry | consecutive sentences of matched length and shape | one contrast between genuinely parallel things | an uneven pair, or one sentence |
| Elegant variation | `the repository`, then `the data layer`, then `the store`, for one class | none where the referent is an identifier | repeat the identifier |
| Nominalization with copula | `the implementation is a reflection of the design`; a chained `permite` plus infinitive | a domain term that is nominal | the actor as subject, the action as verb |
| Circumlocution | `a nivel de`, `en el marco de`, `en lo que respecta a` for a preposition | a phrase that names a layer the sentence is actually about | the preposition: `en` |
| Mixed language | a specimen, term or value in one language inside a text committed to another | a code identifier, a glossary entry, a quotation reproduced verbatim | one language per text, specimens included |
| Mixed register | a text asserts a target and a measurement of the tree without marking which is which, so a reader cannot tell a promise from a mistake | a target declared as one, and a measurement carrying the command that produced it | mark the register per section, or split the two into separate documents |

## Before the first line

| # | Clear before writing | Cost of skipping it |
|---|---|---|
| B1 | Surface, one of: reply, comment, docblock, doc, spec, skill, pull request body, commit body, tracker item, product copy | the surface fixes the rules and the language: instructions and config in English, replies in Spanish, product copy in the product's language and exempt from the register |
| B2 | Whether the document should exist | one that restates code, or duplicates a rule the reader already has, does not get written |
| B3 | What the reader can see | a text written for someone who read the conversation is unreadable to everyone else |
| B4 | Every count: what claim it is the evidence for, and whether it was measured in this session. A count that supports no claim is deleted rather than measured | a count from memory reads like a measured one, and a decorative count rots unnoticed because nothing depended on it |
| B5 | Every path, identifier and command named | prose compiles as prose, so a wrong identifier fails nothing |
| B6 | Whether the rule already lives where the reader is | two copies of one rule keep half each |
| B7 | Which artifacts the change makes stale: comment, docstring, README section, skill | a change that leaves them describing the previous behaviour has not landed |
| B8 | Lede of two to four complete sentences: condition, cause, consequence | a lede opening with a verbless counted phrase |
| B9 | A count is the argument of a verb; counts with detail go to a table | `Ten stacks, 54 branches` standing as a sentence |
| B10 | Facts in tables and labeled lists; prose carries causality | a table that explains why, or a paragraph that lists |
| B11 | One value per cell; `none` in the cell and the reason in its own column | two values in one cell |
| B12 | Unresolved items last, as a labeled list | an open item inside the body |
| B13 | Headings, cells, chips and labels nominal, without gloss or leading article | a verb, a gloss or `The` added to a heading |
| B14 | A consequence takes its own sentence with its own subject | a `, which means` clause |

## Before it ships

| # | Verification | How |
|---|---|---|
| A1 | Every count re-measured against the tree | the command that produced it, run again |
| A2 | Every path and identifier resolved | `ls`, `grep`, or the file opened |
| A3 | No row of the slop register in the text | the register above |
| A4 | Headings declarative, without gloss or leading article | `Name: gloss`, `The name` and a question shape fail |
| A5 | One language per text, specimens included | a specimen in another language goes in a code span or gets translated |
| A6 | Documentation surface of every touched file corrected | read against the new behaviour |
| A7 | Mechanical gate run where one exists | `register-check.py` on markdown, run by hand; a project adds its own gate for code comments where it has one |
| A8 | File read top to bottom, against the tree | the step that catches what nothing else does |

## Audit of existing prose

The deliverable is the finding list. The source stays as it is.

1. Read the whole text. Declare what was read and what was not.
2. Separate prose from data. Code blocks, identifiers, headings and cells fall outside the
   sentence rules. Cells fall inside the one-value rule alone.
3. Name each instance by its row in the register above. An instance that matches none is
   admissible or a gap, and a gap is reported as a gap.
4. Emit one table: `location | current text | row | correct form`.
5. Every finding enters the log below. A finding that matched no row proposes one.

## Log

Open findings, and nothing else. A row enters when a human corrects a pattern or the same
defect appears a second time, and leaves when the human marks it closed. A closed row is not
archived: the rule it produced is its only trace, so a row still here is a finding with no
rule yet.

`Surface` takes one of the values B1 lists. The date is when the row entered, which is the
clock the age runs on.

`Violated` names the register row or the gate the finding failed, and it is what keeps this log
from accepting anything. The audit procedure above already requires naming the row an instance
matches; without a column for it a finding that matches nothing still fits, which is how a
broken reference to a command landed here once instead of in the gate that owns it. A finding
whose cell reads `gap` matches no row and proposes one, and it stays until that row exists.

The session banner reports how many rows sit here and how old the front of the list is, so
a row nobody closes shows its age at every start.

| Date | Surface | Violated | Finding | Uniform correction |
|---|---|---|---|---|

Empty.
