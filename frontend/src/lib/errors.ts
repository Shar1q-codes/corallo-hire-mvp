import type { ProblemDetail } from "./types";

export class ApiError extends Error {
  status: number;
  problem?: ProblemDetail;

  constructor(message: string, status: number, problem?: ProblemDetail) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }
}

export function formatProblem(error: unknown): string {
  if (error instanceof ApiError && error.problem) {
    return `${error.problem.title}: ${error.problem.detail}`;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Request failed.";
}
