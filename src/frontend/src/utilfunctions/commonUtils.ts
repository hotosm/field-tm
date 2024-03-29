export const isInputEmpty = (text: string): boolean => {
  if (typeof text === 'undefined') {
    return true;
  }
  const trimmedText = text.trim();
  return trimmedText === '';
};

export const camelToFlat = (word: string): string => (
  (word = word.replace(/[A-Z]/g, ' $&')), word[0].toUpperCase() + word.slice(1)
);
