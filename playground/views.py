from django.shortcuts import render, redirect
from django.http import HttpResponse
from django import forms
from django.forms import ModelForm
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import render
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from requests.auth import HTTPBasicAuth
import requests
# from .models import StoryEntry
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.auth.hashers import make_password
import os
import os.path
from .forms import *
from .models import *

from gtts import gTTS

# Create your views here.


def index(request):
    stories = storyHistory.objects.filter(user_id=request.user.id)
    return render(request, 'index.html', {'stories': stories})


def login(request):
    if request.method == 'POST':
        user = auth.authenticate(
            username=request.POST['username'], password=request.POST['password'])
        if user is not None:
            auth.login(request, user)
            return redirect('index')
        else:
            return render(request, 'login.html', {'error': 'Username or password is incorrect!'})
    else:
        return render(request, 'login.html')


def register(request):
    if request.method == "POST":
        if request.POST['password1'] == request.POST['password2']:
            try:
                User.objects.get(username=request.POST['username'])
                return render(request, 'register.html', {'error': 'Username is already taken!'})
            except User.DoesNotExist:
                user = User.objects.create_user(
                    request.POST['username'], password=request.POST['password1'], first_name=request.POST['first_name'], last_name=request.POST['last_name'])
                auth.login(request, user)
                return redirect('index')
        else:
            return render(request, 'register.html', {'error': 'Password does not match!'})
    else:
        return render(request, 'register.html')


def logout_user(request):
    if request.user.is_authenticated:
        logout(request)
        return redirect(index)
    else:
        return redirect(index)


def profile_user(request):
    check_user_login(request)

    stories = storyHistory.objects.filter(user_id=request.user.id)

    if request.method == "POST":
        user = User.objects.get(pk=request.user.id)
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']

        if len(request.POST['password1']) > 0:
            if request.POST['password1'] == request.POST['password2']:
                user.password = make_password(request.POST['password1'])
            else:
                return render(request, 'profile.html', {'error': 'Password does not match!'})

        user.save()
        return logout_user(request)

    else:
        return render(request, 'profile.html', {'stories': stories})


def check_user_login(request):
    if not request.user.is_authenticated:
        return redirect(index)

# def search_story(request):

#     if request.method == "POST":
#         form = SearchStoryForm(request.POST)

#         if form.is_valid():
#             your_name = form.cleaned_data["your_name"]
#             your_friend_name = form.cleaned_data["your_friend_name"]
#             story_you_want = form.cleaned_data["story_you_want"]
#             story = generate_story(your_name, your_friend_name, story_you_want)
#             return render(request, 'index.html', {"form": form, "story": story})
#     else:
#         form = SearchStoryForm()
#         return render(request, 'index.html', {"form": form})


def read_story(request, id):
    check_user_login(request)

    stories = storyHistory.objects.filter(id=id)

    return render(request, 'read_story.html', {'stories': stories})


def create_story(request):
    check_user_login(request)

    your_name = ""
    your_friend_name = ""
    story_you_want = ""

    if request.method == "POST":
        your_name = request.POST.get("your_name")
        your_friend_name = request.POST.get("your_friend_name")
        story_you_want = request.POST.get("story_you_want")

        if your_name and your_friend_name and story_you_want:
            search_key_words = (
                your_name + " " + your_friend_name + " " + story_you_want).lower().split(" ")
            contain_bad_words = check_contain_bad_word(search_key_words)

            if contain_bad_words == True:
                message = "You are not allowed to search for these word"
                return render(request, 'create_story.html', {"your_name": your_name, "your_friend_name": your_friend_name, "story_you_want": story_you_want, "message": message})
            else:
                story = generate_story(
                    your_name, your_friend_name, story_you_want)
                # contain_bad_words = check_contain_bad_word(story.split(" "))

                # if contain_bad_words == True:
                #     message = "Story Contained Inappropriated words which are not allowed to be displayed"
                #     return render(request, 'create_story.html', {"your_name": your_name, "your_friend_name": your_friend_name, "story_you_want": story_you_want, "message": message})
                # else:
                userobj = User.objects.get(id=1)
                # saving the story
                history_entry = storyHistory(
                    user_id=userobj,
                    name=your_name,
                    friend_name=your_friend_name,
                    story_topic=story_you_want,
                    generated_story=story
                )
                history_entry.save()

                obj = gTTS(text=story, lang='en', slow=False)
                file_name = "record_sound_" + str(history_entry.id) + ".mp3"
                obj.save(staticfiles_storage.path(file_name))

                return render(request, 'create_story.html', {"your_name": your_name, "your_friend_name": your_friend_name, "story_you_want": story_you_want,
                                                             "story": story, 'history_entry': history_entry})
        else:
            message = "You have to fill all inputs"
            return render(request, 'create_story.html', {"your_name": your_name, "your_friend_name": your_friend_name, "story_you_want": story_you_want, "message": message})

    return render(request, 'create_story.html')


def check_contain_bad_word(search_keywords):
    # search_keywords = search_keywords.lower()

    p = staticfiles_storage.path('bad_words.txt')
    content = open(p).readlines()[0]
    bad_words = content.split(",")
    for keyword in search_keywords:
        if keyword in bad_words:
            return True

    return False


def generate_story(name, friend, story):
    base_url = "https://vicuna-api.aieng.fim.uni-passau.de/v1"
    auth_token = "1"
    endpoint = "/chat/completions"
    url = base_url + endpoint

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": f"Create a child friendly story using protagonist:{name}, friend's name:{friend}, and on the topic:{story}. the story should not contain any  Profanity and Vulgar Language, Explicit Sexual Terms, Violent Actions and Threats, Hate Speech and Offensive Slurs, Drug and Substance References, Graphic or Disturbing Descriptions, Adult Themes, Sensitive Political or Religious, inequality Topics words"
            },

        ]
    }

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code}, Response: {response.text}"


def get_story():
    name = "rat"
    friend = "lamp"
    story = "blueberry"

    story = generate_story(name, friend, story)
    print("Story:", story)


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def checkCodeMatch(request):
    return render(request, "code_match.html")
