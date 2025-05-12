type InviteValues = {
  inviteVia: string;
  user: string[];
  role: string;
};

type ValidationErrors = {
  user?: string;
  role?: string;
};

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function InviteValidation(values: InviteValues) {
  const errors: ValidationErrors = {};

  if (values.user.length === 0) {
    errors.user = 'User is required';
  } else if (
    values.user.length > 0 &&
    values.inviteVia === 'gmail' &&
    values.user.some((email) => !emailPattern.test(email))
  ) {
    errors.user = 'Entered emails must be a Gmail account';
  }

  if (!values.role) {
    errors.role = 'Role is required';
  }

  return errors;
}

export default InviteValidation;
