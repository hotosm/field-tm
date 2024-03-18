export const isInputEmpty = (text: string): boolean => {
  if (typeof text === 'undefined') {
    return true;
  }
  const trimmedText = text.trim();
  return trimmedText === '';
};
