import { describe, expect, it } from "vitest";
import { validateRegistration } from "../utils/validation";

describe("validateRegistration", () => {
  it("accepts a valid registration form", () => {
    expect(
      validateRegistration("AIOps Student", "student@example.com", "StrongPassword123", "StrongPassword123"),
    ).toBeNull();
  });

  it("requires a 12-character password", () => {
    expect(validateRegistration("Student", "student@example.com", "short123", "short123")).toContain(
      "12 characters",
    );
  });

  it("rejects mismatched confirmation", () => {
    expect(
      validateRegistration("Student", "student@example.com", "StrongPassword123", "DifferentPassword123"),
    ).toBe("Passwords do not match.");
  });
});
