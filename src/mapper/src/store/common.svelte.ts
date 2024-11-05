interface AlertDetails {
	variant: 'primary' | 'success' | 'neutral' | 'warning' | 'danger' | null;
	message: string;
}

let alert: AlertDetails | undefined = $state({ variant: null, message: '' });
let projectSetupStep: number | null = $state(null);

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

function getProjectSetupStepStore() {
	return {
		get projectSetupStep() {
			return projectSetupStep;
		},
		setProjectSetupStep: (step: string) => (projectSetupStep = step),
	};
}

export { getAlertStore, getProjectSetupStepStore };
