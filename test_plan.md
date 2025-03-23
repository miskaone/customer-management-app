# Customer Management App Test Plan

Generated: 2025-03-22 11:52:55

## Customer Addition Test

### Step 1: Setup test environment - Launch application and verify initial state

1. Launch customer_manager.py
2. Verify customer list is displayed
3. Verify form is empty

### Step 2: Test basic customer addition functionality

1. Fill out name field with 'Test Customer'
2. Fill out email field with 'test@example.com'
3. Fill out phone field with '555-123-4567'
4. Select or create a directory
5. Click save button
6. Verify customer appears in list

### Step 3: Test validation rules

1. Attempt to save without name field
2. Verify appropriate error message
3. Attempt to save with invalid email format
4. Verify appropriate error message

### Step 4: Test customer editing

1. Select previously created customer
2. Modify details
3. Save changes
4. Verify changes are reflected in list

### Step 5: Test customer deletion

1. Select customer to delete
2. Trigger delete action
3. Confirm deletion in dialog
4. Verify customer is removed from list

## Case Folder Test

### Step 1: Setup test with existing customer

1. Ensure at least one customer exists in system
2. Navigate to case folder tab
3. Select existing customer from dropdown

### Step 2: Test case folder creation

1. Enter case number 'TEST-001'
2. Enter description 'Test Case'
3. Select template from dropdown
4. Click create button
5. Verify case folder appears in list

