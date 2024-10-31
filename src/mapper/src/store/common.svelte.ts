interface AlertDetails {
	variant: 'primary' | 'success' | 'neutral' | 'warning' | 'danger' | null;
	message: string;
}

let alert: AlertDetails | undefined = $state({ variant: null, message: '' });

function getAlertStore() {
	return {
		get alert() {
			return alert;
		},
		setAlert: (alertDetails: AlertDetails) =>
			(alert = { variant: alertDetails.variant, message: alertDetails.message }),
		clearAlert: (alertDetails: AlertDetails) => (alert = { variant: null, message: '' }),
	};
}

export { getAlertStore };
