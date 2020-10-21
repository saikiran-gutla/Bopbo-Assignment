from django.contrib import messages
from django.shortcuts import render
import gspread
import json
import os
import requests
from BopboAssignment.settings import BASE_DIR, MEDIA_ROOT, GOOGLE_CREDENTIALS
from oauth2client.service_account import ServiceAccountCredentials
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


def textus(request):
    if request.method == "POST":
        user_name = request.POST.get('name')
        user_mobile = request.POST.get('mobile')
        user_email = request.POST.get('email')
        user_message = request.POST.get('message')
        user_image = request.FILES.getlist('image')
        print("User image", user_image)
        user_data = [user_name, user_email, user_mobile, user_message]
        write_status = write_data_to_sheet(user_data=user_data, doc_name="Bopbo", sheet_name="Sheet1")
        file_status = store_file_to_drive(uploading_files=user_image,
                                          driver_folder_id="1-z1XeVugB07KMD-40GyMK7bO6FDGqtrJ")
        if write_status and file_status:
            messages.success(request, message='Data Stored Successfully')
        else:
            messages.error(request, 'Data not stored')
    return render(request, 'textus/textus.html', {})


def write_data_to_sheet(user_data, doc_name, sheet_name):
    scope = ['https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(BASE_DIR.joinpath('oauth_cred.json'), scope)
    client = gspread.authorize(credentials)
    sheet = client.open(str(doc_name)).worksheet(str(sheet_name))
    stored = sheet.insert_row(user_data, 2)
    data = sheet.get_all_records()
    if stored['updatedRows'] == 1:
        return True


def store_file_to_drive(uploading_files, driver_folder_id):
    for image in uploading_files:
        path = default_storage.save(image.name, ContentFile(image.read()))
        image_path = os.path.join(MEDIA_ROOT, path)
        headers = {"Authorization": GOOGLE_CREDENTIALS['access_token']}
        para = {
            "name": image.name,
            "parents": [driver_folder_id]
        }
        files = {
            'data': ('metadata', json.dumps(para), 'application/json; charset=UTF-8'),
            'file': open(image_path, "rb")
        }
        response = requests.post(
            "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
            headers=headers,
            files=files
        )
        print(f"Image Response: {response.text}")
        if response.status_code == 200:
            return True
