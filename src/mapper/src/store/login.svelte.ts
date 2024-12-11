type authDetailsType = {
	id: number;
	username: string;
	profile_img: string;
	role: string;
	project_roles: string | null;
	orgs_managed: number[];
};

let authDetails: authDetailsType | null = $state(null);
let isLoginModalOpen: boolean = $state(false);

function getLoginStore() {
	return {
		get getAuthDetails() {
			return authDetails;
		},
		get isLoginModalOpen() {
			return isLoginModalOpen;
		},
		setAuthDetails: (authData: authDetailsType) => {
			authDetails = authData;
			// the react frontend uses redux-persist to store the authDetails in
			// the local storage, so we maintain the same schema to store data here also
			localStorage.setItem(
				'persist:login',
				JSON.stringify({
					authDetails: JSON.stringify(authData),
					_persist: JSON.stringify({ version: -1, rehydrated: true }),
				}),
			);
		},
		retrieveAuthDetailsFromLocalStorage: () => {
			const persistedAuth = localStorage.getItem('persist:login');
			if (!persistedAuth) return;
			authDetails = JSON.parse(JSON.parse(persistedAuth).authDetails);
		},
		toggleLoginModal: (status: boolean) => {
			isLoginModalOpen = status;
		},
		signOut: () => {
			localStorage.removeItem('persist:login');
			authDetails = null;
		},
	};
}

export { getLoginStore };
