# Proposal: cache the reviewer report index

The documentation team wants the report index to load in under 300 ms at
the 95th percentile for 1,000 reports. A background worker will materialize
a listing of report titles, lifecycle states, and current evidence counts.

Each listing is cached for ten minutes under the proposal ID. A successful
write to the first-pass review file invalidates the corresponding cache
entry. Retries and evidence responses remain separate files, as they are
today. Readers will always see the eligibility state and evidence count
for the latest completed update.

The worker reads the proposal, review, and evidence files in sequence. It
writes a new index after reading all three. Readers may continue using
the previous index until the next build finishes.

For the pilot, compare the current and cached implementations using the
first 200 proposals returned by each implementation's listing API.
Record request wall time for successful requests. Entries that time out
or return an error are excluded from the latency calculation. Run each
configuration once on the same machine. A passing latency result is
sufficient to make the cache the default.
