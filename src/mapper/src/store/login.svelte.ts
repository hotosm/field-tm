type authDetailsType = {
	id: number;
	username: string;
	picture: string;
	role: string;
	// Here we omit project_roles and orgs_managed as they are not needed
	// for mapping. The token refresh endpoints do not call the db for this
	// data, in order to be more performant / separate concerns.
	// project_roles: string | null;
	// orgs_managed: number[];
};

import { refreshCookies } from '$lib/utils/login';

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
		},
		toggleLoginModal: (status: boolean) => {
			isLoginModalOpen = status;
		},
		signOut: async () => {
			authDetails = null;
			// Re-add temp auth cookies
			await refreshCookies();
		},
	};
}

export { getLoginStore };
