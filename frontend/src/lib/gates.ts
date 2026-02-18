const risk = "risk_signals";
const interview = "interview_guidance";

export function gateLabel(type: string): string {
  if (type === risk) {
    return "Risk Signals require Intent Hypotheses to be reviewed first.";
  }
  if (type === interview) {
    return "Interview Validation Guidance requires Intent Hypotheses and Risk Signals to be reviewed first.";
  }
  return "";
}

export function isArtifactUnlocked(type: string, viewed: Record<string, string | null>): boolean {
  if (type === "intent_hypotheses") {
    return true;
  }
  if (type === risk) {
    return Boolean(viewed.intent_hypotheses);
  }
  if (type === interview) {
    return Boolean(viewed.intent_hypotheses && viewed.risk_signals);
  }
  return false;
}
