export const isStatusSuccess = (status: number): boolean => {
  if (status < 300) {
    return true;
  }
  return false;
};
