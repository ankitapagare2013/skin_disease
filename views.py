from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate, login as auth_login
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import cv2
import numpy as np
import os


def home(request):
    return render(request, 'home.html')


def login(request):
    if request.method == "POST":
        un = request.POST['username']
        pw = request.POST['password']
        user = authenticate(request, username=un, password=pw)
        if user is not None:
            auth_login(request, user)
            return redirect('/profile')  # Redirect to profile after successful login
        else:
            msg = 'Invalid Username/Password'
            form = AuthenticationForm()
            return render(request, 'login.html', {'form': form, 'msg': msg})
    else:
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to the login page after successful signup
            return redirect('/login')  # This redirects to the login page
    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {'form': form})


def profile(request):
    if request.method == 'POST' and request.FILES.get('uploaded_image'):
        uploaded_image = request.FILES['uploaded_image']

        # Validate that the uploaded file is an image
        if not uploaded_image.content_type.startswith('image/'):
            return render(request, 'profile.html', {'error_message': 'Invalid file type. Please upload an image.'})

        fs = FileSystemStorage()
        filename = fs.save(uploaded_image.name, uploaded_image)
        uploaded_image_url = fs.url(filename)

        # Load the uploaded image
        image_path = os.path.join(settings.MEDIA_ROOT, filename)
        img = cv2.imread(image_path)

        if img is None:
            return render(request, 'profile.html', {'error_message': 'Could not read the image file.'})
        
        # Resize the image
        img_resize = cv2.resize(img, (183, 275))
        if len(img_resize.shape) == 2:
            img_resize = cv2.cvtColor(img_resize, cv2.COLOR_GRAY2BGR)
        img_normalize = img_resize / 255.0
        img_normalize = (img_normalize * 255).astype(np.uint8)

        # Dimension convert
        img_dim = np.expand_dims(img_normalize, axis=0)
        print(img_dim)
        
        # Convert to grayscale and apply blur
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Threshold
        _, thresh = cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        result_img = img.copy()

        detected_areas = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Adjust conditions based on your uploaded image characteristics
            if w > 10 and h > 10:
                detected_areas.append((x, y, w, h))

                # Draw rectangle and annotate on the image
                cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(result_img, f"W:{w}, H:{h}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        # Save processed image
        processed_filename = f'processed_{filename}'
        processed_path = os.path.join(settings.MEDIA_ROOT, processed_filename)
        cv2.imwrite(processed_path, result_img)
        processed_image_url = fs.url(processed_filename)

        # Prepare output data
        areas_info = [f"Width={w} px, Height={h} px" for (x, y, w, h) in detected_areas]

        return render(request, 'profile.html', {
            'uploaded_image_url': uploaded_image_url,
            'processed_image_url': processed_image_url,
            'areas_info': areas_info
        })

    return render(request, 'profile.html')
   
