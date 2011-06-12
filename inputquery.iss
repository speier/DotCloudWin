var
 UserPage: TInputQueryWizardPage;
 
UserPage := CreateInputQueryPage(wpUserInfo,
    'Personal Information', 'Who are you?',
    'Please specify your name and email, then click Next.');
    UserPage2.Add('Name:', False);
    UserPage2.Add('Last Name:', False);
    UserPage2.Add('Email:', False);
    UserPage2.Add('System Name:', False);