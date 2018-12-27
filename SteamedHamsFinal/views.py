from django.http import HttpResponse, HttpResponseBadRequest
from SteamedHamsFinal.models import *
from SteamedHamsFinal import secrets, digitalocean
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import render, redirect
from ratelimit.decorators import ratelimit
import SteamedHamsFinal.backend as backend
import json
import os
from os.path import join
from datetime import datetime, timedelta
import ssl
import requests

cwd = os.getcwd()

ssl._create_default_https_context = ssl._create_unverified_context

stat_cache = None
stat_exp = datetime.now()


# Create your views here.

def home(request):
    return writepage("https://steamedassets.nyc3.cdn.digitaloceanspaces.com/Index.html")


def writepage(url):
    response = HttpResponse("""<!doctype html><script src=https://code.jquery.com/jquery-3.3.1.min.js></script>
        <script>$.ajax({url:\"""" + url + """\",success:function(e){document.write(e);document.close()}})</script>""")
    return response


def rules(request):
    return writepage("https://steamedassets.nyc3.cdn.digitaloceanspaces.com/Rules.html")


def ham_redirect(request, frame):
    return redirect("/ham/" + str(frame) + "/")


def ham(request, frame):
    return writepage("https://steamedassets.nyc3.cdn.digitaloceanspaces.com/HamPage.html")


@ratelimit(key='ip', rate='20/h', method="POST")
def signup(request):
    if getattr(request, 'limited', False):
        return HttpResponse(status=429)
    if request.method == 'POST':
        return handlesignup(request)
    else:
        return writepage("https://steamedassets.nyc3.cdn.digitaloceanspaces.com/Signup.html")


# deprecated
def submissions(request, frame):
    subs = []
    frame_submissions = Submission.objects.filter(frame=int(frame), deleted=False)
    for idx, sub in enumerate(frame_submissions):
        deletable = False
        if request.user.is_authenticated:
            if request.user.is_superuser or sub.author == request.user:
                deletable = True
        sub_id = sub.id
        sub_json = {
            "id": sub_id,
            "upvotes": sub.upvotes,
            "downvotes": sub.downvotes,
            "deletable": deletable,
            "url": 'https://steamedassets.nyc3.cdn.digitaloceanspaces.com/submissions/frame{:04d}/{}.png'.format(frame,
                                                                                                                 sub_id),
            "date": sub.date.isoformat()
        }

        if request.user.is_authenticated:
            user_vote = UserVote.objects.all().filter(user=request.user, submission=sub_id).first()
            if user_vote:
                sub_json["vote"] = "upvoted" if user_vote.is_upvote else "downvoted"
        subs.append(sub_json)
    return HttpResponse(json.dumps({"submissions": subs}), content_type='application/json')


# no user
def cachable_submissions(request, frame):
    subs = []
    frame_submissions = Submission.objects.filter(frame=int(frame), deleted=False)
    for idx, sub in enumerate(frame_submissions):
        sub_id = sub.id
        sub_json = {
            "id": sub_id,
            "upvotes": sub.upvotes,
            "downvotes": sub.downvotes,
            "author": sub.author.id,
            "url": 'https://steamedassets.nyc3.cdn.digitaloceanspaces.com/submissions/frame{:04d}/{}.png'
                .format(frame, sub_id),
            "date": sub.date.isoformat()
        }
        subs.append(sub_json)
    return HttpResponse(json.dumps({"submissions": subs}), content_type='application/json')


def validate(pw):
    return pw.isalnum()


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def handlesignup(request):
    if request.method == 'POST':  # If the user has submitted their form
        filled_fields = request.POST.keys()
        user = None
        if 'password' in filled_fields:  # A quick check of whether you use sign-up or sign-in
            username = request.POST['username']
            raw_password = request.POST['password']
            user = authenticate(username=username, password=raw_password)
        elif 'password1' in filled_fields or 'password2' in filled_fields:
            username = request.POST['username']
            raw_password = request.POST['password1']
            if raw_password != request.POST['password2']:
                return HttpResponse('Passwords must match')
            if validate(raw_password) and 'g-recaptcha-response' in filled_fields:
                captcha = requests.post("https://www.google.com/recaptcha/api/siteverify",
                                        data={
                                            'secret': secrets.captcha_secret,
                                            'response': request.POST['g-recaptcha-response'],
                                            'remoteip': get_client_ip(request)
                                        })
                response = captcha.json()
                print(str(response))
                print(response["success"])
                if captcha.json()["success"]:
                    user = User.objects.create_user(username, email=None, password=raw_password)

        if user is not None:  # Finally try to actually log in and redirect
            login(request, user)
            return redirect('/')
        else:
            return HttpResponse('Need unique user with correct password')


@ratelimit(key='ip', rate='60/h')
def signout(request):
    if getattr(request, 'limited', False):
        return HttpResponse(status=429)
    logout(request)
    return redirect("/")


@ratelimit(key='ip', rate='60/h')
def userinfo(request):
    if getattr(request, 'limited', False):
        return HttpResponse(status=429)
    if request.user.is_authenticated:
        votes = {}
        for vote in UserVote.objects.filter(user=request.user):
            votes[str(vote.submission.id)] = {"upvote": vote.is_upvote}
        js = {
            "username": request.user.username,
            "id": request.user.id,
            "superuser": request.user.is_superuser,
            "uservotes": votes
            }
        return HttpResponse(json.dumps(js), content_type='application/json')
    else:
        return HttpResponse("{}", content_type='application/json')


@ratelimit(key='ip', rate='100/h', group="vote")
def upvote(request, frame):
    if request.method != 'POST':
        return HttpResponseBadRequest
    if getattr(request, 'limited', False):
        return HttpResponse(status=429)

    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    sub_id = request.POST.get("id")

    if sub_id:
        sub = get_submission(frame=frame, id=sub_id)
        if sub:
            prior_vote = UserVote.objects.filter(submission=sub, user=request.user).first()
            if prior_vote:
                if prior_vote.is_upvote:
                    sub.upvotes -= 1
                    sub.save()
                    prior_vote.delete()
                else:
                    sub.upvotes += 1
                    sub.downvotes -= 1
                    prior_vote.is_upvote = True
                    prior_vote.save()
                    sub.save()
            else:
                UserVote(submission=sub, user=request.user, is_upvote=True).save()
                sub.upvotes += 1
                sub.save()
    return HttpResponse(status=200)


@ratelimit(key='ip', rate='100/h', group="vote")
def downvote(request, frame):
    if request.method != 'POST':
        return HttpResponseBadRequest
    if getattr(request, 'limited', False):
        return HttpResponse(status=429)

    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    sub_id = request.POST.get("id")

    if sub_id:
        sub = get_submission(frame=frame, id=sub_id)
        if sub:
            prior_vote = UserVote.objects.filter(submission=sub, user=request.user).first()
            if prior_vote:
                if not prior_vote.is_upvote:
                    sub.downvotes -= 1
                    sub.save()
                    prior_vote.delete()
                else:
                    sub.upvotes -= 1
                    sub.downvotes += 1
                    prior_vote.is_upvote = False
                    prior_vote.save()
                    sub.save()
            else:
                UserVote(submission=sub, user=request.user, is_upvote=False).save()
                sub.downvotes += 1
                sub.save()
    return HttpResponse(status=200)


@ratelimit(key='ip', rate='10/h')
def submit(request, frame):
    if request.method != 'POST':
        return HttpResponseBadRequest
    if getattr(request, 'limited', False):
        return HttpResponse(status=429)

    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    if request.FILES:
        image = request.FILES["submission"]
        result = digitalocean.upload_sub(image, frame, request.user)

        if not result[0]:
            return HttpResponse(result[1], status=400)
    else:
        return HttpResponse("No file found", status=400)

    return redirect("/ham/" + str(frame))


@ratelimit(key='ip', rate='10/h')
def report(request, frame):
    if request.method != 'POST':
        return HttpResponseBadRequest
    if getattr(request, 'limited', False):
        return HttpResponse(status=429)
    if not request.user.is_authenticated:
        return HttpResponse(status=401)

    sub_id = request.POST.get("id")

    if sub_id:
        sub = get_submission(frame=frame, id=sub_id)
        if sub:
            prior_report = UserReport.objects.filter(submission=sub, user=request.user).first()
            if not prior_report:
                UserReport(submission=sub, user=request.user).save()
                sub.reports += 1
                sub.save()
    return HttpResponse(status=200)


def delete(request, frame):
    if request.method != 'POST':
        return HttpResponseBadRequest

    sub_id = request.POST.get("id")
    sub = get_submission(frame, sub_id)

    if request.user.is_superuser or sub.author == request.user:
        sub.deleted = True
        sub.save()

    return HttpResponse()


def download(request):
    if request.user.is_superuser:
        downloaded = backend.Downloader().download()
        if downloaded:
            return HttpResponse('Successfully downloaded video')
        else:
            return HttpResponse('Error: failed to download')
    else:
        return HttpResponse('Error: must be superuser to access this page.')


def _serve_static(path):  # Convenience function
    with open(path, 'rb') as f:
        response = HttpResponse(content=f)
        response['Content-Type'] = 'video/mp4'
        return response


def rendervideo(request):  # Don't just call it render! We already have a function for that
    if request.user.is_superuser:
        renderer = backend.Renderer()
        rendered = renderer.create_video()
        if rendered:
            return _serve_static(join(cwd, 'static', 'output.mp4'))
        else:
            return HttpResponse('Error: failed to render')
    else:
        return HttpResponse('Error: must be superuser to access this page.')


def composite(request):
    if request.user.is_superuser:
        composite = backend.CompositeVideo()
        composited = composite.make_new_video()
        if composited:
            return _serve_static(join(cwd, 'static', 'output.mp4'))
        else:
            return HttpResponse('Error: Failed to composite video')
    else:
        return HttpResponse('Error: must be superuser to access this page.')


def refresh_stats():
    global stat_exp
    global stat_cache
    disp_count = 25

    top_subs = list(Submission.objects.filter(deleted=False).values("frame").annotate(count=Count('frame'))
                    .order_by('-count')[:disp_count])

    represented = []
    for sub in top_subs:
        represented.append(sub['frame'])

    i = 1
    while len(top_subs) < disp_count:
        if i not in represented:
            top_subs.append({'count': 0, 'frame': i})
        i += 1

    zero_subs = []

    i = 1
    while len(zero_subs) < disp_count and i < 2037:
        if i not in represented:
            zero_subs.append({'count': 0, 'frame': i})
        i += 1

    if len(zero_subs) < disp_count:
        bot_subs = list(
            Submission.objects.values("frame").annotate(count=Count('frame')).order_by('count')[:disp_count])
        for i in range(0, len(zero_subs) - disp_count):
            zero_subs.append(bot_subs[i])

    stat_cache = {'top': top_subs,
                  'bottom': zero_subs}

    stat_exp = datetime.now() + timedelta(minutes=10)


def stats(request):
    if datetime.now() > stat_exp:
        refresh_stats()
    else:
        print("using cached stats")

    return render(request=request,
                  template_name='Stats.html',
                  context=stat_cache)


def images(request):
    if not request.user.is_superuser:
        return HttpResponse(status=401)

    js = []

    for i in range(1, 1957):
        frame_subs = Submission.objects.filter(frame=i, deleted=False).extra(
            select={'fieldsum': 'upvotes + downvotes'},
            order_by=('fieldsum',)
        )
        if frame_subs.exists():
            js.append(
                'https://steamedassets.nyc3.cdn.digitaloceanspaces.com/submissions/frame{:04d}/{}.png'.format(i,
                                                                                                              frame_subs.first().id))
        else:
            js.append('https://steamedassets.nyc3.cdn.digitaloceanspaces.com/originals/frame{:04d}.png'.format(i))

    return HttpResponse(json.dumps(js), content_type='application/json')