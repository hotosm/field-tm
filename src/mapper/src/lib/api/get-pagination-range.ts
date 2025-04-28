export const DOTS = '...';

type paginationRange = { totalCount: number; pageSize: number; siblingCount?: number; currentPage: number };

export function getPaginationRange({ totalCount, pageSize, siblingCount = 1, currentPage }: paginationRange) {
	const totalPageCount = Math.ceil(totalCount / pageSize);
	const totalPageNumbers = siblingCount * 2 + 5;

	const range = (start: number, end: number) => {
		const length = end - start + 1;
		/*
          Create an array of certain length and set the elements within it from
          start value to end value.
        */
		return Array.from({ length }, (_, idx) => idx + start);
	};

	if (totalPageNumbers >= totalPageCount) {
		return range(1, totalPageCount);
	}

	const leftSiblingIndex = Math.max(currentPage - siblingCount, 1);
	const rightSiblingIndex = Math.min(currentPage + siblingCount, totalPageCount);

	const shouldShowLeftDots = leftSiblingIndex > 2;
	const shouldShowRightDots = rightSiblingIndex < totalPageCount - 2;

	if (!shouldShowLeftDots && shouldShowRightDots) {
		const leftItemCount = 3 + 1 * siblingCount;
		const leftRange = range(1, leftItemCount);
		return [...leftRange, DOTS, totalPageCount];
	}

	if (shouldShowLeftDots && !shouldShowRightDots) {
		const rightItemCount = 3 + 2 * siblingCount;
		const rightRange = range(totalPageCount - rightItemCount + 1, totalPageCount);
		return [1, DOTS, ...rightRange];
	}

	if (shouldShowLeftDots && shouldShowRightDots) {
		const middleRange = range(leftSiblingIndex, rightSiblingIndex);
		return [1, DOTS, ...middleRange, DOTS, totalPageCount];
	}

	return [];
}
