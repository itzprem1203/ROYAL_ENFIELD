import os
import psycopg2
from django.http import JsonResponse
from django.shortcuts import redirect, render
import json
from datetime import datetime
from app.models import UserLogin,BackupSettings

def home(request):
    error_message = ''
    if request.method == 'POST':
        username = request.POST.get('user')
        password = request.POST.get('password')

        # Get or create UserLogin instance with id=1
        user_login, created = UserLogin.objects.get_or_create(id=1, defaults={'username': username, 'password': password})

        # Update username and password if already exists
        if not created:
            user_login.username = username
            user_login.password = password
            user_login.save()

        # Check username and password for redirection
        if username in ['admin', 'o', 'saadmin'] and password == username:
            return redirect('index')  # Redirect after successful login without backing up
        else:
            error_message = 'Invalid username or password'

        # Pass the backup date to the template
        return render(request, "app/home.html", {
            'error_message': error_message,
        })

    elif request.method == 'GET':
        try:
            # Get the latest BackupSettings entry
            backup_settings = BackupSettings.objects.order_by('-id').first()

            if backup_settings:
                # Print both backup_date and confirm_backup values in the terminal
                print('ID:', backup_settings.id)
                print('Backup Date:', backup_settings.backup_date)
                print('Confirm Backup:', backup_settings.confirm_backup)
                

                # Pass the values to the context
                context = {
                    'backup_date': backup_settings.backup_date,
                    'confirm_backup': backup_settings.confirm_backup,
                    'id': backup_settings.id
                }

            else:
                # If no BackupSettings found, pass empty values
                context = {
                    'backup_date': None,
                    'confirm_backup': None,
                    'id': None
                }

            return render(request, 'app/home.html', context)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request, 'app/home.html')
