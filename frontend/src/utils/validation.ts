export function validateRegistration(
  fullName: string,
  email: string,
  password: string,
  confirmPassword: string,
): string | null {
  if (fullName.trim().length < 2) return "Enter your full name.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return "Enter a valid email address.";
  if (password.length < 12) return "Password must contain at least 12 characters.";
  if (password !== confirmPassword) return "Passwords do not match.";
  return null;
}
