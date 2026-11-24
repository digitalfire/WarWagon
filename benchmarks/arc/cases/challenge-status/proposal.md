# Proposal: summarize challenge status in the review workspace

The architecture team wants a compact status card for imported ARC
artifacts. A maintainer should be able to tell within 30 seconds whether a
proposal can proceed without opening each JSON file. The card will show
review completion, open challenges, and a decision badge.

The console will display a green Approved badge once every reviewer role
has a current support or conditional verdict and none of the imported
dispositions are marked unresolved or needs-evidence. It will derive the
badge directly from the imported records. The console will open any
partial bundle a user selects, including a review report by itself.

Dispositions will be assigned to challenges by matching the reviewer role
and proposal title. If multiple dispositions match, the browser will use
the most recently modified file. After a disposition is selected, the
evidence drawer will show the latest imported response for that challenge.
The selected disposition will stay active when a replacement response is
imported. To make reviewer names easier to trust, the card will display
Verified maintainer when the disposition has a nonempty maintainer field
and the digest of its referenced challenge matches the imported challenge.

The pilot will use the same six recorded challenge bundles in both the old
JSON workflow and the new workspace. All six are complete and have one
response and one disposition. Record time to read the card and agreement
with the most recent disposition on disk. Ship the badge when the median
time drops below 30 seconds and agreement is at least five of six.
