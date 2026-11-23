# Review-index ARC pilot result

This is one evaluation-science review per model on the same [frozen
proposal](cases/review-index/proposal.md). The calls used the same ARC
system prompt, local Ollama endpoint, and RTX 5090. Candidate call order
was randomized. The [checklist](cases/review-index/checklist.json) was
finalized before inference and was kept out of both model inputs.

One Codex assessment pass applied the five criteria to the responses
with their model labels removed. Judgments were saved before revealing
the mapping. The assessor also helped prepare the case and run the
models, so this is a label-masked assessment rather than an independently
administered blind trial.

| Candidate | Provider-reported model | Criteria met | Attempt elapsed time | Reported tokens |
| --- | --- | ---: | ---: | ---: |
| review-1 | `gemma4:26b` | 1/5 | 12.13 s | 1,860 |
| review-2 | `qwen3.8:27b` | 3/5 | 35.92 s | 3,338 |

Both reviews proposed repeated measurement. Review 2 also identified
the different proposal samples and called for matched workloads, and it
required reporting timeouts and errors separately. Review 1 recognized
the survivorship bias but proposed folding failures into a latency
penalty. Both missed the missing cache invalidation triggers and the
possibility of mixed revisions in an index build.

This is descriptive evidence for one proposal, one assessor, and one
attempt per model. Durations include local model loading and provider
overhead. The scores do not establish a general model ranking; repeat
on fresh held-out cases with independent judges and controlled execution
before changing reviewer assignments.

The raw run, label-masked packet, and individual judgments were
preserved in the local handoff workspace. SHA-256 digests:

- Raw run: `b24973d0d4ac62c7ab65ae43e20001c0a9283ce7103f28f976b6eb311faf7ce3`
- Label-masked packet: `f3bc95f1e36026d7ca19d9ceb143fbe4c02040c3f499182aded5503dfaa7ac4e`
- Judgments: `2b311618e55a85ce7d5fd84b7637f8e933fc72002f08936f340d472294160930`
