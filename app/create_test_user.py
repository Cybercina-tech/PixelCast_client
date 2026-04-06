"""
Script to create a test user for login testing.
Run with: python manage.py shell < create_test_user.py
Or: python manage.py shell
Then paste the code below.
"""

from accounts.models import User

# Create a test user
username = 'siavash'
email = 'siavash@example.com'
password = 'testpass123'  # Change this to your desired password

# Check if user already exists
if User.objects.filter(username=username).exists():
    print(f'User "{username}" already exists.')
    user = User.objects.get(username=username)
    print(f'  - Email: {user.email}')
    print(f'  - Is Active: {user.is_active}')
    print(f'  - Role: {user.get_role_display()}')
    print('\nTo reset password, run:')
    print(f'  user.set_password("{password}")')
    print('  user.save()')
else:
    # Create new user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        full_name='Siavash Test User',
        role='admin',  # Options: 'admin', 'manager', 'viewer'
        is_active=True
    )
    print(f'User "{username}" created successfully!')
    print(f'  - Email: {email}')
    print(f'  - Password: {password}')
    print(f'  - Role: {user.get_role_display()}')
    print(f'  - Is Active: {user.is_active}')

