export function isValidUrl(url: string) {
  try {
    const { protocol } = new URL(url);
    return protocol === 'http:' || protocol === 'https:';
  } catch (error) {
    return false;
  }
}
