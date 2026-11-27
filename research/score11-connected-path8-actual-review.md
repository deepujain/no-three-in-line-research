# Connected path8 actual review

Decision: accept the complete negative for all six fixed eight-edge patches. Valid incumbent remains 156.

The source-pinned run completed all six templates, 12096 quota records, and 1306 post-exclusion geometry decisions with zero witnesses. Its normal 30-second/256-MiB gate exited zero with clean cleanup, no trigger or monitor error, outer time 0.155042 seconds and peak sampled RSS 52144 KiB. All 18 receipt pins, complete status, counter partitions and absence of witness files were independently checked.

A shorter independent proof establishes the result without relying on the cap-five exclusions or factor-generation implementation. Each patch retains 150 fixed source points and frees 20 rectangle cells. Every cell was independently checked against the retained-point pairs using exact integer determinants. Exactly six cells per patch avoid every retained secant. Thus no completion can have more than 150+6=156 points. This excludes both requested cardinalities without checking interactions among added cells.

`data/score11-connected-path8-independent-actual-audit.json`, SHA-256 `5c73cc24f5aaad9189c95a7f8191fe27bea854fd088f3b9edd01482aa4c2a97b`, stores every safe cell and explicit retained-pair determinant certificates for all 84 blocked cells. Each of the 36 safe cells was tested against all 11175 retained pairs. The independent audit took 0.034 seconds. The earlier independent path arithmetic establishes exhaustive coverage of all six length-eight intervals containing the chosen three-edge cover.

The closure applies only to these six original connected source patches. It does not exclude every eight-deletion repair, larger connected patches, other source configurations, or unrestricted n79 existence. No repeat allocation is needed for this scope.
