from django.shortcuts import render, redirect
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import FarmerProfile
from .forms import FarmerProfileForm, PhoneVerificationForm
import json
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from .models import Prediction



# ---------------- HOME ----------------
def home(request):
    predictions = Prediction.objects.none()

    if request.user.is_authenticated:
        predictions = Prediction.objects.filter(user=request.user)

    return render(request, "home.html", {"predictions": predictions})
# ---------------- SIGNUP ----------------
def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        password = request.POST.get("password")

        # Validation
        if not name or not email or not phone or not password:
            messages.error(request, "Please fill all required fields.")
            return redirect("recommender:signup")

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return redirect("recommender:signup")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Account already exists with this email.")
            return redirect("recommender:signup")

        # Create User
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        # Split name
        if " " in name:
            first, last = name.split(" ", 1)
        else:
            first, last = name, ""

        user.first_name = first
        user.last_name = last
        user.save()

        # Create Profile
        UserProfile.objects.create(user=user, phone=phone)

        login(request, user)
        messages.success(request, "Account Created Successfully! Welcome!")
        return redirect("recommender:predict")

    return render(request, "recommender/signup.html")


# ---------------- LOGIN ----------------
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login Successful!")
            return redirect("recommender:predict")
        else:
            messages.error(request, "Invalid Email or Password!")
            return redirect("recommender:login")

    return render(request, "recommender/login.html")

from .ml.loder import predict_one, load_bundle
import time
from django.contrib.auth.decorators import login_required

@login_required
def predict_view(request):
    if not request.user.is_authenticated:
        messages.error(request, "Please login first.")
        return redirect("recommender:login")

    feature_order = load_bundle()["feature_cols"]
    result = None
    last_data = None
    prediction_time = None

    if request.method == "POST":
        data = {}
        try:
            for c in feature_order:
                data[c] = float(request.POST.get(c))
        except:
            messages.error(request, "Please enter valid numeric values.")
            return redirect("recommender:predict")

        # ⏱ Start timer
        start = time.time()

        label = predict_one(data)

        # ⏱ End timer
        end = time.time()
        prediction_time = round(end - start, 4)

        Prediction.objects.create(
            user=request.user,
            **data,
            predicted_label=label
        )

        result = label
        last_data = data
        messages.success(request, f"Recommended Crop : {label.title()}")

    return render(request, "predict.html", locals())

# ---------------- LOGOUT ----------------
def logout_view(request):
    logout(request)
    messages.success(request, "Logout Successfully!")
    return redirect("recommender:home")



@login_required

def user_history_view(request):
    predictions = Prediction.objects.filter(user=request.user)
    return render(request, "history.html", {'predictions': predictions})

from django.shortcuts import redirect, get_object_or_404
@login_required

def user_delete_prediction(request, id):
    prediction = get_object_or_404(Prediction, id=id, user=request.user)
    prediction.delete()
    messages.success(request, "Entry removed from history")
    return redirect("recommender:user_history")

@login_required
def profile_form(request):

    # Get existing profile
    profile = None
    try:
        profile = FarmerProfile.objects.get(user=request.user)
    except FarmerProfile.DoesNotExist:
        profile = None

    # Check session profile
    session_profile_id = request.session.get('profile_id')
    if not profile and session_profile_id:
        try:
            profile = FarmerProfile.objects.get(id=session_profile_id)
        except FarmerProfile.DoesNotExist:
            profile = None

    is_update = profile is not None

    
    if request.method == 'POST':

        form = FarmerProfileForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():

            profile = form.save(commit=False)

            # Attach logged-in user
            if request.user.is_authenticated:
                profile.user = request.user

            # Handle multiple choice fields
            profile.current_crops = request.POST.getlist('current_crops')
            profile.help_needed = request.POST.getlist('help_needed')

            profile.save()

            # Store profile id in session
            request.session['profile_id'] = profile.id

            # Send JSON response for AJAX
            return JsonResponse({
                "success": True,
                "message": "Profile updated successfully!" if is_update else "Profile created successfully!",
                "redirect_url": reverse('recommender:profile_preview', args=[profile.id])
            })

        else:
            # Return validation errors
            errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}

            return JsonResponse({
                "success": False,
                "errors": errors
            })

    form = FarmerProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
        'is_update': is_update,
        'crop_choices': FarmerProfile.CROP_CHOICES,
        'help_choices': FarmerProfile.HELP_CHOICES,
    }

    return render(request, 'recommender/profile_form.html', context)


def profile_preview(request, profile_id):
    profile = get_object_or_404(FarmerProfile, id=profile_id)
    
    context = {
        'profile': profile,
        'crops_display': profile.get_crops_display(),
        'help_display': profile.get_help_display(),
    }
    return render(request, 'recommender/profile_preview.html', context)


@require_POST
def send_verification_code(request):
    data = json.loads(request.body)
    phone = data.get('phone')
    profile_id = request.session.get('profile_id')
    
    if not phone:
        return JsonResponse({'success': False, 'error': 'Phone number is required'})
    
    try:
        if profile_id:
            profile = FarmerProfile.objects.get(id=profile_id)
        else:
            profile = FarmerProfile.objects.create(phone=phone, full_name='Temp')
            request.session['profile_id'] = profile.id
        
        profile.phone = phone
        code = profile.generate_verification_code()
        
        # In production, send SMS here
        # For demo, we'll return the code
        print(f"Verification code for {phone}: {code}")
        
        return JsonResponse({
            'success': True,
            'message': 'Verification code sent!',
            'demo_code': code  # Remove in production
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def verify_phone(request):
    data = json.loads(request.body)
    code = data.get('code')
    profile_id = request.session.get('profile_id')
    
    if not profile_id:
        return JsonResponse({'success': False, 'error': 'No profile found'})
    
    try:
        profile = FarmerProfile.objects.get(id=profile_id)
        
        if profile.verify_phone(code):
            return JsonResponse({'success': True, 'message': 'Phone verified successfully!'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid verification code. Please try again.'})
    except FarmerProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profile not found'})


def get_country_fields(request):
    country = request.GET.get('country', '')
    is_india = country == 'india'
    
    return JsonResponse({
        'show_india_fields': is_india,
        'fields': {
            'pan': is_india,
            'aadhaar': is_india,
            'pm_kisan': is_india,
        }
    })

@login_required
def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        # 1. Check old password
        if not user.check_password(old_password):
            messages.error(request, "Old password is incorrect ❌")
            return redirect('recommender:change_password')

        # 2. Match new passwords
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match ❌")
            return redirect('recommender:change_password')

        # 3. Minimum 8 characters
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters ⚠️")
            return redirect('recommender:change_password')

        # 4. Save new password
        user.set_password(new_password)
        user.save()

        # Keep user logged in
        update_session_auth_hash(request, user)

        messages.success(request, "Password updated successfully ✅")
        return redirect('recommender:change_password')

    return render(request, 'change_password.html')
from django.contrib.auth.models import User


# Admin Login View
def admin_login(request):
    if request.method == "POST":   # ✅ Proper indentation
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user and user.is_staff:
            login(request, user)
            return redirect('/admin-dashboard/?success=1')

        else:
            messages.error(request, "Invalid admin credentials")

    return render(request, 'admin.html')


from django.db.models import Count
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from .models import Prediction

def admin_dashboard(request):

    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')

    user_count = User.objects.count()
    total_predictions = Prediction.objects.count()

    # ✅ Crop data (FINAL)
    crop_counts = (
        Prediction.objects
        .values('predicted_label')
        .annotate(count=Count('predicted_label'))
        .order_by('-count')
    )

    crop_data = [
        (c['predicted_label'], c['count'])
        for c in crop_counts
    ]

    # Last 7 days
    dates = []
    last_7_days = []

    for i in range(6, -1, -1):
        day = timezone.now() - timedelta(days=i)

        count = Prediction.objects.filter(
            created_at__date=day.date()
        ).count()

        dates.append(day.strftime("%d %b"))
        last_7_days.append(count)

    context = {
        'user_count': user_count,
        'total_predictions': total_predictions,
        'crop_data': crop_data,   # ✅ ONLY this
        'dates': dates,
        'last_7_days': last_7_days,
    }

    return render(request, 'admin_dashboard.html', context)

def user_view(request):

    # Only admin can access
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('admin_login')

    total_users = User.objects.count()
    admin_users = User.objects.filter(is_staff=True).count()
    normal_users = User.objects.filter(is_staff=False).count()

    users = User.objects.all().order_by('-date_joined')

    context = {
        'total_users': total_users,
        'admin_users': admin_users,
        'normal_users': normal_users,
        'users': users
    }

    return render(request, 'user_view.html', context)

# Logout
def admin_logout(request):
    logout(request)
    return redirect('admin_login')


# views.py

from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from .models import MessageToGovernment, MessageToAgriculture

User = get_user_model()

@login_required
def user_management(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to view this page.")
        return redirect('recommender:admin_dashboard')  # or home

    users = User.objects.all().order_by('-date_joined')
    total_users = users.count()
    admin_users = users.filter(is_staff=True).count()
    normal_users = total_users - admin_users

    context = {
        'users': users,
        'total_users': total_users,
        'admin_users': admin_users,
        'normal_users': normal_users,
    }
    return render(request, 'recommender/user_management.html', context)  # update path if needed


@login_required
def delete_user(request, user_id):
    if not request.user.is_staff:
        messages.error(request, "Only admins can delete users.")
        return redirect('recommender:user_management')  # or your url name

    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        messages.error(request, "You cannot delete yourself.")
        return redirect('recommender:user_management')

    if request.method == 'POST':
        user.delete()
        messages.success(request, f"User {user.username} has been deleted successfully.")
        return redirect('recommender:user_management')

    return render(request, 'recommender/user_confirm_delete.html', {'user': user})


# Message views (you can put them in the same page or separate)
@login_required
def send_message_govt(request):
    if request.method == 'POST':
        message_text = request.POST.get('govt_message')
        photo = request.FILES.get('govt_photo')

        if message_text.strip():
            MessageToGovernment.objects.create(
                user=request.user,
                message=message_text,
                photo=photo
            )
            messages.success(request, "Message successfully sent to Government / Higher Authority!")
        else:
            messages.error(request, "Message cannot be empty.")

        return redirect('recommender:user_management')  # or wherever you want

    return redirect('recommender:user_management')


@login_required
def send_message_agri(request):
    if request.method == 'POST':
        message_text = request.POST.get('agri_message')
        photo = request.FILES.get('agri_photo')

        if message_text.strip():
            MessageToAgriculture.objects.create(
                user=request.user,
                message=message_text,
                photo=photo
            )
            messages.success(request, "Message successfully sent to Agriculture Officer!")
        else:
            messages.error(request, "Message cannot be empty.")

        return redirect('recommender:user_management')

    return redirect('recommender:user_management')

from django.shortcuts import render

# views.py
def prediction_analysis_view(request, crop):
    # Example data - expand for all crops
    if crop == 'rice':
        crop_data = {
            'image': 'https://example.com/rice.jpg',
            'tips': 'Maintain 5 cm water during tillering, use neem for early pests.',
            'growth_rate': '4–6 tons/ha',
            'growth_months': {
                'labels': ['Sowing', 'Tillering', 'Panicle', 'Flowering', 'Maturity'],
                'data': [10, 40, 80, 100, 70]
            },
            'states': [
                {'name': 'Uttar Pradesh', 'lat': 27.0, 'lng': 80.0, 'share': 13.8},
                {'name': 'Telangana', 'lat': 18.0, 'lng': 79.0, 'share': 11.6},
                {'name': 'West Bengal', 'lat': 22.5, 'lng': 88.0, 'share': 10.7},
                {'name': 'Punjab', 'lat': 31.0, 'lng': 75.0, 'share': 9.5},
                {'name': 'Chhattisgarh', 'lat': 21.0, 'lng': 82.0, 'share': 6.9},
                {'name': 'Odisha', 'lat': 20.0, 'lng': 85.0, 'share': 6.3},
            ],
            'pests': [
                {'name': 'Brown Plant Hopper', 'desc': 'Sucks sap → hopperburn, virus spread', 'control': 'Neem oil spray or Imidacloprid; keep field clean'},
                {'name': 'Yellow Stem Borer', 'desc': 'Dead heart in young plants, white ear head later', 'control': 'Cartap hydrochloride or pheromone traps; remove stubbles'},
                {'name': 'Leaf Folder', 'desc': 'Folds leaves → reduced photosynthesis', 'control': 'Trichogramma release or Quinalphos spray'},
            ],
            'insecticides_pesticides': [
                'Neem oil / Bio-pesticides every 10-15 days',
                'Trichoderma for seed treatment',
                'Imidacloprid for hoppers (use judiciously)'
            ],
            'nutrition': [  # per 100g cooked white rice approx
                {'name': 'Protein', 'value': '2.7g'},
                {'name': 'Calcium', 'value': '3-10mg'},
                {'name': 'Potassium', 'value': '35-55mg'},
                {'name': 'Iron', 'value': '0.4-1.9mg'},
                {'name': 'Vitamin B1', 'value': '0.02mg'},
            ]
        }
    else:
        crop_data = {}  # handle other crops similarly

    return render(request, 'recommender/prediction_analysis.html', {
        'crop': crop,
        'crop_data': crop_data,
    })