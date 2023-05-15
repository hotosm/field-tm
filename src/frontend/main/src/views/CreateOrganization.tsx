import React, { useState } from 'react';
import { InputLabel } from '@mui/material';
import CoreModules from '../shared/CoreModules';

const CreateOrganizationForm: React.FC = () => {
  const [organizationName, setOrganizationName] = useState('');
  const [website, setWebsite] = useState('');
  const [description, setDescription] = useState('');
  const [dropdownValue, setDropdownValue] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleOrganizationNameChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setOrganizationName(event.target.value);
  };

  const handleWebsiteChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setWebsite(event.target.value);
  };

  const handleDescriptionChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDescription(event.target.value);
  };

  const handleDropdownChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setDropdownValue(event.target.value as string);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setOrganizationName('');
    setWebsite('');
    setDescription('');
    setDropdownValue('');
    setSelectedFile(null);
  };

  return (
    <CoreModules.Box
      sx={{ display: 'flex', flexDirection: 'column', alignItems: 'start', background: '#f0efef', flex: 1, gap: 3 }}
    >
      <CoreModules.Box
        sx={{
          paddingTop: '2%',
          justifyContent: 'flex-start',
          marginLeft: '7.5%',
        }}
      >
        <CoreModules.Typography variant="condensed">CREATE NEW ORGANIZATION</CoreModules.Typography>
      </CoreModules.Box>
      <CoreModules.Box
        sx={{
          width: 600,
          padding: 5,
          cursor: 'pointer',
          background: '#ffff',
          marginLeft: '7.5%',
          borderRadius: 2,
        }}
      >
        <form onSubmit={handleSubmit}>
          <CoreModules.TextField
            variant="outlined"
            label="Organization Name"
            value={organizationName}
            onChange={handleOrganizationNameChange}
            fullWidth
            margin="normal"
          />
          <CoreModules.TextField
            label="Website"
            value={website}
            onChange={handleWebsiteChange}
            fullWidth
            margin="normal"
          />
          <CoreModules.TextField
            label="Description"
            value={description}
            onChange={handleDescriptionChange}
            multiline
            fullWidth
            margin="normal"
          />
          <CoreModules.FormControl fullWidth margin="normal">
            <InputLabel id="dropdown-label">Dropdown</InputLabel>
            <CoreModules.Select labelId="dropdown-label" value={dropdownValue} onChange={handleDropdownChange}>
              <CoreModules.MenuItem value="">Select an option</CoreModules.MenuItem>
              <CoreModules.MenuItem value="option1">Option 1</CoreModules.MenuItem>
              <CoreModules.MenuItem value="option2">Option 2</CoreModules.MenuItem>
              <CoreModules.MenuItem value="option3">Option 3</CoreModules.MenuItem>
            </CoreModules.Select>
          </CoreModules.FormControl>
          <CoreModules.Input type="file" onChange={handleFileChange} style={{ display: 'none' }} />
          <label htmlFor="file">
            <CoreModules.Button variant="contained" component="span">
              Choose File
            </CoreModules.Button>
          </label>
          <CoreModules.Typography>{selectedFile?.name || 'No file chosen'}</CoreModules.Typography>

          <CoreModules.Button
            type="submit"
            variant="outlined"
            color="error"
            size="large"
            sx={{ minWidth: 'fit-content', width: 'auto', fontWeight: 'bold' }}
          >
            Submit
          </CoreModules.Button>
        </form>
      </CoreModules.Box>
    </CoreModules.Box>
  );
};

export default CreateOrganizationForm;
