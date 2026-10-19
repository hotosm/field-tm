export type FetchFn = (url: string, init?: RequestInit) => Promise<Response>;

export async function readJsonFile(file: File): Promise<unknown> {
  try {
    return JSON.parse(await file.text());
  } catch {
    throw new Error(`${file.name} is not valid GeoJSON`);
  }
}

export async function fetchJson(
  url: string,
  init?: RequestInit,
  fetchFn: FetchFn = fetch,
): Promise<unknown> {
  const res = await fetchFn(url, init);
  if (!res.ok) throw new Error(`Could not load ${url} (HTTP ${res.status})`);
  return res.json();
}

export function download(filename: string, content: string, type = "application/geo+json") {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
