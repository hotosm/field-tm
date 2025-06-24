export const isInputEmpty = (text: string): boolean => {
  if (typeof text === 'undefined') {
    return true;
  }
  const trimmedText = text.trim();
  return trimmedText === '';
};

export const camelToFlat = (word: string): string => (
  (word = word.replace(/[A-Z]/g, ' $&')),
  word[0].toUpperCase() + word.slice(1)
);

export const isStatusSuccess = (status: number): boolean => {
  if (status < 300) {
    return true;
  }
  return false;
};

// get date N days ago
export const dateNDaysAgo = (NDays: number): string => {
  return new Date(new Date().getTime() - NDays * 24 * 60 * 60 * 1000).toISOString();
};

// extract month & day in MM/DD format for chart date labels
export const getMonthDate = (date: string): string => {
  const splittedDate = date?.split('T')[0]?.split('-');
  return `${splittedDate[1]}/${splittedDate[2]}`;
};

// generates an array of date strings for last 30 days
export const generateLast30Days = (): string[] => {
  const last30Days: string[] = [];
  const today = new Date();

  for (let i = 0; i < 30; i++) {
    const date = new Date();
    date.setDate(today.getDate() - i);
    last30Days.push(date.toISOString().split('T')[0]);
  }

  return last30Days;
};

// checks if object or array is empty
export function isEmpty(obj: any): boolean {
  if (Array.isArray(obj)) {
    return obj.length === 0;
  }
  return Object.keys(obj).length === 0;
}
