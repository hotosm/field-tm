export function getTimeDiff(date: Date) {
	const now = new Date(new Date().toISOString());
	return Math.floor((now.getTime() - date.getTime()) / 1000);
}

// Convert a UTC date string to a 'time ago' string, in minutes, hours, or days.
export function convertDateToTimeAgo(dateToFormat: string): string {
	// Convert dateToFormat string to UTC date
	const theDate = new Date(dateToFormat);
	const timeDiff = getTimeDiff(theDate);

	let timeAgo;
	if (timeDiff < 3600) {
		// less than an hour
		timeAgo = `${Math.floor(timeDiff / 60)} minutes ago`;
	} else if (timeDiff < 86400) {
		// less than 24 hours
		timeAgo = `${Math.floor(timeDiff / 3600)} hours ago`;
	} else {
		// 24 hours or more
		timeAgo = `${Math.floor(timeDiff / 86400)} days ago`;
	}

	return timeAgo;
}
