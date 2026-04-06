"""
Test script to debug login issues.
Run with: python manage.py shell < test_login.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Screengram.settings')
django.setup()

from accounts.models import User
from django.contrib.auth import authenticate

username = 'siavash'
password = input(f'Enter password for user "{username}": ')

print(f'\n=== Testing login for user: {username} ===\n')

# Find user
user_obj = User.objects.filter(username__iexact=username).first()
if not user_obj:
    user_obj = User.objects.filter(email__iexact=username).first()

if not user_obj:
    print(f'❌ User "{username}" not found in database!')
    print('\nAvailable users:')
    for u in User.objects.all()[:10]:
        print(f'  - Username: "{u.username}", Email: "{u.email}", Active: {u.is_active}')
else:
    print(f'✅ User found:')
    print(f'   Username: "{user_obj.username}"')
    print(f'   Email: "{user_obj.email}"')
    print(f'   Is Active: {user_obj.is_active}')
    print(f'   Has Usable Password: {user_obj.has_usable_password()}')
    
    # Test authenticate
    print(f'\n=== Testing authenticate() ===')
    auth_user = authenticate(username=user_obj.username, password=password)
    if auth_user:
        print(f'✅ authenticate() succeeded')
    else:
        print(f'❌ authenticate() failed')
    
    # Test check_password
    print(f'\n=== Testing check_password() ===')
    if user_obj.check_password(password):
        print(f'✅ check_password() succeeded')
    else:
        print(f'❌ check_password() failed')
        print(f'   (This means the password is incorrect)')
    
    # Show password hash info (for debugging)
    print(f'\n=== Password Hash Info ===')
    print(f'   Password hash: {user_obj.password[:50]}...')
    print(f'   Hash algorithm: {user_obj.password.split("$")[0] if "$" in user_obj.password else "Unknown"}')

