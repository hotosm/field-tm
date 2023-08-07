interface ISidebarContent {
    id: number;
    name: string;
    slug: string;
    type?: string;
}


const SidebarContent: ISidebarContent[] = [
    {
        id: 1,
        name: 'Project Description',
        slug: 'project-description'
    },
    {
        id: 2,
        name: 'Form Update',
        slug: 'form-update'
    },
    {
        id: 3,
        name: 'Update Project Boundary',
        slug: 'update-project-boundary'
    },
]

export default SidebarContent