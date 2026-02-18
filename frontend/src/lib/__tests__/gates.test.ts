import { describe, expect, it } from "vitest";

import { isArtifactUnlocked } from "../gates";

describe("artifact gates", () => {
  it("enforces intent -> risk -> interview order", () => {
    const noneViewed = {
      intent_hypotheses: null,
      risk_signals: null,
      interview_guidance: null
    };
    expect(isArtifactUnlocked("intent_hypotheses", noneViewed)).toBe(true);
    expect(isArtifactUnlocked("risk_signals", noneViewed)).toBe(false);
    expect(isArtifactUnlocked("interview_guidance", noneViewed)).toBe(false);

    const intentViewed = {
      intent_hypotheses: "2026-01-01T00:00:00Z",
      risk_signals: null,
      interview_guidance: null
    };
    expect(isArtifactUnlocked("risk_signals", intentViewed)).toBe(true);
    expect(isArtifactUnlocked("interview_guidance", intentViewed)).toBe(false);

    const riskViewed = {
      intent_hypotheses: "2026-01-01T00:00:00Z",
      risk_signals: "2026-01-01T00:01:00Z",
      interview_guidance: null
    };
    expect(isArtifactUnlocked("interview_guidance", riskViewed)).toBe(true);
  });
});
