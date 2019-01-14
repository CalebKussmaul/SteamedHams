from django.http import HttpResponse, HttpResponseBadRequest
from SteamedHamsFinal.models import *
from SteamedHamsFinal import secrets, digitalocean
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import render, redirect
from ratelimit.decorators import ratelimit
from django.core.cache import cache
from django.urls import reverse
from django.http import HttpRequest
from django.utils.cache import get_cache_key
from django.views.decorators.cache import cache_page, never_cache
import SteamedHamsFinal.backend as backend
import json
import os
from os.path import join
from datetime import datetime, timedelta
import ssl
import requests

cwd = os.getcwd()

ssl._create_default_https_context = ssl._create_unverified_context

# stat_cache = None
# stat_exp = datetime.now()
# def writepage(url):
#     response = HttpResponse("""<!doctype html><script src=https://code.jquery.com/jquery-3.3.1.min.js></script>
#         <script>$.ajax({url:\"""" + url + """\",success:function(e){document.open();document.write(e);document.close()}})</script>""")
#     return response


def loader_io(request):
    return HttpResponse("loaderio-a121e3b9103b84461b5f933652cff7c7")


def favicon(request):
    return redirect("https://steamedassets.nyc3.cdn.digitaloceanspaces.com/favicon.ico", permanent=True)


@cache_page(60 * 60 * 24)
def home(request):
    return render(request, 'Index.html')
    # return writepage("https://steamedassets.nyc3.cdn.digitaloceanspaces.com/Index.html")


@cache_page(60 * 60 * 24)
def rules(request):
    return render(request, 'Rules.html')
    # return writepage("https://steamedassets.nyc3.cdn.digitaloceanspaces.com/Rules.html")


@cache_page(60 * 60 * 24)
def ham_redirect(request, frame):
    return redirect("/ham/" + str(frame) + "/")


@cache_page(60 * 60 * 24)
def ham(request, frame=12):
    return render(request, 'HamPage.html')
    # return writepage("https://steamedassets.nyc3.cdn.digitaloceanspaces.com/HamPage.html")


@cache_page(60 * 60 * 24)
@ratelimit(key='ip', rate='20/h', method="POST")
def signup(request):
    if getattr(request, 'limited', False):
        return HttpResponse(status=429)
    if request.method == 'POST':
        return handlesignup(request)
    else:
        # return writepage("https://steamedassets.nyc3.cdn.digitaloceanspaces.com/Signup.html")
        return render(request, 'Signup.html')


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
@cache_page(60 * 5)
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


@cache_page(60 * 5)
def stats(request):
    # global stat_exp
    # global stat_cache
    disp_count = 25
    print("refreshing stats")

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

    # stat_exp = datetime.now() + timedelta(minutes=10)

    return render(request=request,
                  template_name='Stats.html',
                  context=stat_cache)


@never_cache
@cache_page(0)
@ratelimit(key='ip', rate='60/h')
def my_stuff(request):
    if not request.user.is_authenticated:
        return render(request=request,
                      template_name='NoStuff.html')

    my_votes = UserVote.objects.filter(user=request.user)
    total_my_votes = my_votes.count()
    my_upvotes = my_votes.filter(is_upvote=True).count()

    subs = Submission.objects.filter(author=request.user, deleted=False)

    sub_votes = UserVote.objects.filter(submission__in=subs)
    total_sub_votes = my_votes.count()
    sub_upvotes = sub_votes.filter(is_upvote=True).count()

    context = {
        'down': total_my_votes-my_upvotes,
        'up': my_upvotes,
        'subs': subs,
        'sub_down': total_sub_votes-sub_upvotes,
        'sub_up': sub_upvotes,
    }

    return render(request=request,
                  template_name='MyStuff.html',
                  context=context)


def validate(pw):
    try:
        pw.decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


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
        elif 'username1' in filled_fields and 'password1' in filled_fields and 'password2' in filled_fields:
            username = request.POST['username1']
            raw_password = request.POST['password1']
            if raw_password != request.POST['password2']:
                return HttpResponse('Passwords must match')
            if validate(raw_password) and 'g-recaptcha-response' in filled_fields:
                if User.objects.filter(username=username).exists():
                    return redirect('/signup/?msg=Username already taken ' +
                                    '(note, usernames don\'t actually matter for anything)')
                captcha = requests.post("https://www.google.com/recaptcha/api/siteverify",
                                        data={
                                            'secret': secrets.captcha_secret,
                                            'response': request.POST['g-recaptcha-response'],
                                            'remoteip': get_client_ip(request)
                                        })
                if captcha.json()["success"]:
                    user = User.objects.create_user(username, email=None, password=raw_password)
                else:
                    return redirect('/signup/?msg=Captcha error')
            else:
                return redirect('/signup/?msg=Invalid form')
        if user is not None:  # Finally try to actually log in and redirect
            login(request, user)
            return redirect('/')
        else:
            return redirect('/signup/?msg=Error logging in')


@never_cache
@ratelimit(key='ip', rate='60/h')
def signout(request):
    if getattr(request, 'limited', False):
        return HttpResponse(status=429)
    logout(request)
    return redirect("/")


@never_cache
@cache_page(0)
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


@never_cache
@ratelimit(key='user', rate='100/h', group="vote")
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
                    sub.score -= 1
                    sub.save()
                    prior_vote.delete()
                else:
                    sub.upvotes += 1
                    sub.downvotes -= 1
                    sub.score += 2
                    prior_vote.is_upvote = True
                    prior_vote.save()
                    sub.save()
            else:
                UserVote(submission=sub, user=request.user, is_upvote=True).save()
                sub.upvotes += 1
                sub.score += 1
                sub.save()
    return HttpResponse(status=200)


@never_cache
@ratelimit(key='user', rate='100/h', group="vote")
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
                    sub.score += 1
                    sub.save()
                    prior_vote.delete()
                else:
                    sub.upvotes -= 1
                    sub.downvotes += 1
                    sub.score -= 2
                    prior_vote.is_upvote = False
                    prior_vote.save()
                    sub.save()
            else:
                UserVote(submission=sub, user=request.user, is_upvote=False).save()
                sub.downvotes += 1
                sub.score += 1
                sub.save()
    return HttpResponse(status=200)


@never_cache
@ratelimit(key='user', rate='10/h')
def submit(request, frame):
    if request.method != 'POST':
        return HttpResponseBadRequest
    if getattr(request, 'limited', False):
        return HttpResponse(status=429)

    if not request.POST:
        return HttpResponse(status=401)

    if 'g-recaptcha-response' not in request.POST:
        return HttpResponse(status=400)
    captcha = requests.post("https://www.google.com/recaptcha/api/siteverify",
                            data={
                                'secret': secrets.captcha_upload_secret,
                                'response': request.POST['g-recaptcha-response'],
                                'remoteip': get_client_ip(request)
                            })
    if not captcha.json()["success"]:
        return HttpResponse(status=400)

    if request.FILES:
        image = request.FILES["submission"]
        result = digitalocean.upload_sub(image, frame, request.user)

        if not result[0]:
            return HttpResponse(result[1], status=400)
    else:
        return HttpResponse("No file found", status=400)

    expire_page(request.META, reverse(cachable_submissions, args=[frame]))
    return redirect("/ham/"+str(frame)+"/")


@never_cache
@ratelimit(key='user', rate='10/h')
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


@never_cache
def delete(request, frame):
    if request.method != 'POST':
        return HttpResponseBadRequest

    sub_id = request.POST.get("id")
    sub = get_submission(frame, sub_id)

    if request.user.is_superuser or sub.author == request.user:
        sub.deleted = True
        sub.save()

    expire_page(request.META, reverse(cachable_submissions, args=[frame]))
    return HttpResponse()


@never_cache
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


def expire_page(request_meta, path):
    request = HttpRequest()
    request.META = request_meta
    # request.META = {'SERVER_NAME': request_meta.SERVER_NAME, 'SERVER_PORT': request_meta.SERVER_PORT}
    request.LANGUAGE_CODE = 'en-us'
    request.path = path
    key = get_cache_key(request)
    if key in cache:
        print("invalidating cache entry")
        cache.delete(key)


@never_cache
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


@never_cache
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


@never_cache
def images(request, password):
    # if not request.user.is_superuser:
    #     return HttpResponse(status=401)

    # make accesible via script (ie: not loggd in)
    if password != secrets.images_password:
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
