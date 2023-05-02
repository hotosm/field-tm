
interface OrganizationValues {
    logo: string;
    name: string;
    description: string;
    url: string;
    type: number;
}
interface ValidationErrors {
    logo?: string;
    name?: string;
    description?: string;
    url?: string;
    type?: string;
}

function OrganizationAddValidation(values: OrganizationValues) {
    const errors: ValidationErrors = {};

    if (!values?.logo) {
        errors.logo = 'Logo is Required.';
    }
    if (!values?.name) {
        errors.name = 'Name is Required.';
    }
    if (!values?.description) {
        errors.description = 'Description is Required.';
    }
    if (!values?.url) {
        errors.url = 'Organization Url is Required.';
    }
    if (!values?.type) {
        errors.type = 'Type is Required.';
    }

    return errors;
}

export default OrganizationAddValidation;
