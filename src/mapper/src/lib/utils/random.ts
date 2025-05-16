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

export function getNewOsmId() {
	// NOTE 32-bit int is max supported by standard postgres Integer
	// 0 to 1073741823
	const getRandBits = (n: number) => Math.floor(Math.random() * 2 ** n);
	const newId = -Math.abs(getRandBits(30)); // Ensure it's negative (not in OSM)
	return newId;
}
