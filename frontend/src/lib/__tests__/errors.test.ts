import { describe, expect, it } from "vitest";

import { ApiError, formatProblem } from "../errors";

describe("formatProblem", () => {
  it("renders RFC9457 problem details plainly", () => {
    const err = new ApiError("bad", 422, {
      type: "x",
      title: "Validation Error",
      status: 422,
      detail: "Request validation failed."
    });
    expect(formatProblem(err)).toContain("Validation Error");
    expect(formatProblem(err)).toContain("Request validation failed.");
  });
});
