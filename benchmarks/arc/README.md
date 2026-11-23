# ARC reviewer-quality pilot cases

The review-index case is an evaluation-science exercise for comparing
reviews of the same short proposal. It concerns documentation index
correctness and measurement.

- [Proposal](cases/review-index/proposal.md)
- [Assessor checklist](cases/review-index/checklist.json)
- [First pilot result](review-index-pilot.md)

Use only the proposal as reviewer input. Keep the checklist out of the
model context. Verify the proposal's SHA-256 digest before running. Use
the same role, ARC prompt, endpoint, and execution settings for all
candidates. Record response model labels, finish reasons, validation
status, usage, and elapsed time. Retain invalid results separately.

Mask model labels before grading. Apply the exact same checklist and
give each judgment a rationale anchored in the response. Report
inconclusive items and unresolved reviewer disagreements separately.
Keep this case out of prompt development if using it as a holdout.
Once results inform revisions to the review prompt, use a fresh holdout
for claims about the revised prompt.

This single case can demonstrate a comparison procedure. Estimating
reviewer quality requires diverse held-out cases, repeated runs, and
independent assessment.
