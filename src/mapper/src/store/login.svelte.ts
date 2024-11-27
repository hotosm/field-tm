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
