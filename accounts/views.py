from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, Score, Handicap
from .forms import CustomUserCreationForm, ScoreSubmissionForm
import json
import matplotlib.pyplot as plt
import io
import urllib
import base64

import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.files.uploadedfile import InMemoryUploadedFile
from .forms import UploadFileForm


import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Handicap
from .forms import UploadFileForm

User = get_user_model()


# ✅ User Registration
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')  # Ensure 'dashboard' exists in urls.py
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


# ✅ User Login
def user_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'accounts/login.html')


# ✅ User Logout
def user_logout(request):
    logout(request)
    return redirect('login')


# ✅ Submit Score & Update Handicap
@login_required
def submit_score(request):
    if request.method == "POST":
        form = ScoreSubmissionForm(request.POST)
        if form.is_valid():
            score = form.save(commit=False)  
            score.player = request.user  
            score.save()  

            # ✅ Ensure Handicap is updated
            calculate_handicap(request.user, score.score)

            messages.success(request, "Score submitted successfully!")
            # return redirect("dashboard")  
    else:
        form = ScoreSubmissionForm()

    return render(request, "accounts/submit_score.html", {"form": form})  # Ensure template exists


# ✅ Generate Score Chart
def generate_score_chart(scores):
    dates = [score.date_played.strftime("%Y-%m-%d") for score in scores]
    score_values = [score.score for score in scores]

    plt.figure(figsize=(8, 4))
    plt.plot(dates, score_values, marker='o', linestyle='-', color='b', label='Scores')
    plt.xlabel("Date")
    plt.ylabel("Score")
    plt.title("Score Trend Over Time")
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    encoded_image = base64.b64encode(buffer.getvalue()).decode()
    buffer.close()
    return f"data:image/png;base64,{encoded_image}"


# ✅ Dashboard View
@login_required
def dashboard(request):
    handicap = Handicap.objects.filter(player=request.user).first()
    scores = Score.objects.filter(player=request.user).order_by('-date_played')

    labels = [score.date_played.strftime("%Y-%m-%d") for score in scores]
    data = [score.score for score in scores]

    context = {
        'handicap': handicap,
        'scores': scores,
        'chart_labels': json.dumps(labels),
        'chart_data': json.dumps(data),
    }
    return render(request, 'accounts/dashboard.html', context)


# ✅ Leaderboard View
# def leaderboard(request):
#     # top_players = CustomUser.objects.order_by('handicap__value')[:10]  # ✅ Fix sorting issue
#     top_players = CustomUser.objects.filter(handicap__value__isnull=False).order_by('handicap__value')[:10]
#     return render(request, 'accounts/leaderboard.html', {'top_players': top_players})


from django.core.paginator import Paginator
from django.shortcuts import render
from .models import CustomUser  # Import your user model

def leaderboard(request):
    all_players = CustomUser.objects.filter(handicap__value__isnull=False).order_by('handicap__value')

    # Set pagination (20 players per page)
    paginator = Paginator(all_players, 50)  
    page_number = request.GET.get('page')  # Get page number from URL
    page_obj = paginator.get_page(page_number)  # Get the page

    return render(request, 'accounts/leaderboard.html', {'page_obj': page_obj})




# ✅ Handicap Calculation
# def calculate_handicap(player, score):
#     """
#     Calculates and updates the player's handicap.
#     """
#     categories = [
#         {"min_hcp": 1, "max_hcp": 5, "par": 72, "factor": 0.1},
#         {"min_hcp": 6, "max_hcp": 12, "par": 73, "factor": 0.2},
#         {"min_hcp": 13, "max_hcp": 18, "par": 75, "factor": 0.3},
#         {"min_hcp": 19, "max_hcp": 28, "par": 76, "factor": 0.4},
#     ]

#     handicap_instance, created = Handicap.objects.get_or_create(player=player)  # ✅ Ensure it exists
#     current_hcp = handicap_instance.value if handicap_instance else 0.0

#     for cat in categories:
#         if cat["min_hcp"] <= current_hcp <= cat["max_hcp"]:
#             course_par = cat["par"]
#             # course_par = 72
#             reduction_factor = cat["factor"]
#             break
#     else:
#         return  

#     if score > course_par:
#         new_hcp = current_hcp + 0.1
#     else:
#         difference = course_par - score
#         new_hcp = current_hcp - (reduction_factor * difference)

#     new_hcp = round(new_hcp, 2)  

#     handicap_instance.value = new_hcp
#     handicap_instance.save()

#     return new_hcp  

def calculate_handicap(player, score):
    """
    Calculates and updates the player's handicap.
    """
    categories = [
        {"min_hcp": 1, "max_hcp": 5, "par": 72, "factor": 0.1},
        {"min_hcp": 6, "max_hcp": 12, "par": 73, "factor": 0.2},
        {"min_hcp": 13, "max_hcp": 18, "par": 75, "factor": 0.3},
        {"min_hcp": 19, "max_hcp": 28, "par": 76, "factor": 0.4},
    ]

    handicap_instance, created = Handicap.objects.get_or_create(player=player)  
    current_hcp = handicap_instance.value if handicap_instance else 0.0

    for cat in categories:
        if cat["min_hcp"] <= current_hcp <= cat["max_hcp"]:
            course_par = cat["par"]
            reduction_factor = cat["factor"]
            break
    else:
        return  

    if score > course_par:
        new_hcp = current_hcp + 0.1
    else:
        difference = course_par - score
        new_hcp = current_hcp - (reduction_factor * difference)

    new_hcp = round(new_hcp, 2)  

    # Ensure new_hcp does not exceed 28
    new_hcp = min(new_hcp, 28)

    handicap_instance.value = new_hcp
    handicap_instance.save()

    return new_hcp  



# @login_required
def upload_players(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["file"]
            
            try:
                # Read file directly from memory
                df = pd.read_excel(file)

                # Ensure required columns exist
                if "NAMES" not in df.columns or "Handicap" not in df.columns:
                    messages.error(request, "Invalid file format! Ensure columns are 'NAMES' and 'Handicap'.")
                    return redirect("upload_players")

                for _, row in df.iterrows():
                    full_name = row["NAMES"].strip()
                    handicap_value = float(row["Handicap"])

                    # Extract first name and create username/email
                    first_name = full_name.split()[0]
                    username = f"{first_name.lower()}@enugugolf.com"
                    password = first_name  # Default password

                    # Check if user exists, else create
                    user, created = User.objects.get_or_create(username=username, defaults={
                        "first_name": first_name,
                        "last_name": " ".join(full_name.split()[1:]),  # Store remaining part of the name
                        "email": username,
                    })

                    if created:
                        user.set_password(password)  # Set default password
                        user.save()

                    # Assign handicap
                    handicap, _ = Handicap.objects.get_or_create(player=user, defaults={"value": handicap_value})
                    handicap.value = handicap_value
                    handicap.save()

                messages.success(request, "Players uploaded successfully!")
            except Exception as e:
                messages.error(request, f"Error processing file: {e}")
            return redirect("login")
    
    else:
        form = UploadFileForm()
    
    return render(request, "accounts/upload_players.html", {"form": form})

