export function getDeviceId() {
	if (typeof localStorage === 'object') {
		const item = localStorage.getItem('deviceid');
		if (item) {
			return item;
		} else {
			const uuid = crypto.randomUUID();
			localStorage.setItem('deviceid', uuid);
			return uuid;
		}
	} else {
		return crypto.randomUUID();
	}
}
