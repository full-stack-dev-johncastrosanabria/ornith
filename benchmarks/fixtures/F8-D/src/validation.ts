import { ValidationError } from "./errors.ts";

/** Parses an optional integer parameter: digits only, within [min, max]; `fallback` when absent. */
export function intParam(field: string, raw: string | undefined, fallback: number, min: number, max: number): number {
  if (raw === undefined) return fallback;
  if (!/^\d+$/.test(raw)) throw new ValidationError(field, `${field} must be a whole number`);
  const value = Number(raw);
  if (value < min || value > max) throw new ValidationError(field, `${field} must be between ${min} and ${max}`);
  return value;
}
