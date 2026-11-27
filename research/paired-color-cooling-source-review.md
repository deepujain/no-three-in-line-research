# Controlled cooling variant: source review

Approved one n79 seed279401 soft25 pilot under Root's owned 30s/256MiB guard, fresh output and no implicit retry. Source SHA256 `fe1ba4da0e312056db5a46a8f94a38c24ca77f8c61c927747cd8db25b9876d83`. All source pins match. Independently ran all six baseline/cooling tiny tests: passed in 0.033s. No n79 run was launched during this review.

The variant imports the frozen legal initializer, exact conflict score and reversible proposal/delta functions. Its dynamic change is the positive temperature schedule T=4+(0.02-4)*clamp(elapsed/seconds,0,1). The initializer, uniform proposed row swaps and best-state reset policy remain the same. Metropolis acceptance changes with temperature, so both accepted states and subsequent random-number consumption can diverge from the baseline; one paired run supplies an empirical comparison, not statistical evidence of general improvement.

Tests cover schedule endpoints, midpoint, clamping and invalid durations, tiny deterministic runs and independent final determinant scores. The final best state is checked by both geometry validators. Final-current score is reported but its point set is not saved, so independent artifact audit can directly establish the best score only. Score zero is required for a valid full certificate; positive scores remain invalid full states.

The strict paired-color family, absence of completeness/connectivity claims, current/best storage without growing history, possible O(n^3) final-validator storage, and outer guard ownership of hard resource limits are unchanged from the baseline review.
