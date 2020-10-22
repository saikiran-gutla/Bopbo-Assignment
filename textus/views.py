from django.contrib import messages
from django.shortcuts import render
import gspread
import json
import os
import requests
from google.auth.exceptions import TransportError
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
        write_status = write_data_to_sheet_upload_file(request, user_data=user_data, doc_name="Bopbo",
                                                       sheet_name="Sheet1",
                                                       uploading_files=user_image,
                                                       driver_folder_id="1-z1XeVugB07KMD-40GyMK7bO6FDGqtrJ")
        if write_status:
            messages.success(request, message='Data Stored Successfully')
        else:
            messages.error(request, 'Data not stored')
    return render(request, 'textus/textus.html', {})


def write_data_to_sheet_upload_file(request, user_data, doc_name, sheet_name, uploading_files, driver_folder_id):
    """
    This method writes the data to the Google SpreadSheet and uploads the files to Google Drive.
    request (obj): Request type object
    user_data (list): Form user information to store into Sheet
    doc_name (str): Name of the Document to store the UserData
    sheet_name (str): Name of the Sheet in the Document to store UserData
    uploading_files (obj): Multiple files to upload data
    driver_folder_id (str): GoogleDrive FolderId to store data
    :return: returns True if data is successfully stored
    """
    try:
        # GOOGLE SHEETS CONNECTION CODE GOES HERE
        scope = ['https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(BASE_DIR.joinpath('oauth_cred.json'), scope)
        client = gspread.authorize(credentials)
        sheet = client.open(str(doc_name)).worksheet(str(sheet_name))
        # WRITING DATA TO SHEETS CODE GOES HERE
        stored = sheet.insert_row(user_data, 2)
        data = sheet.get_all_records()
        # FILE UPLOAD CODE GOES HERE
        for image in uploading_files:
            path = default_storage.save(image.name, ContentFile(image.read()))
            image_path = os.path.join(MEDIA_ROOT, path)
            headers = {"Authorization": GOOGLE_CREDENTIALS['access_token']}
            params = json.dumps({
                "name": image.name,
                "parents": [driver_folder_id]
            })
            files = {
                'data': ('metadata', params, 'application/json; charset=UTF-8'),
                'file': open(image_path, "rb")
            }
            response = requests.post(
                "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart",
                headers=headers,
                files=files
            )
            print(f"Image Response: {response.text}")
        if stored['updatedRows']:
            return True
    except TransportError:
        messages.success(request,
                         message='Failed Establishing Connection.'
                                 ' Please Genereate New Access Token and specify in Settings file')
