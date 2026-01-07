
export function normalize(s?: string | null | undefined) {
  return s?.toLowerCase().replace(/\s+/g, " ").trim() ?? "";
}

export function matchesSearch(
  search: string,
  ...fields: (string | null | undefined)[]
) {
  if (!search) return true;

  const q = normalize(search);

  return fields.some(f =>
    normalize(f).includes(q)
  );
}