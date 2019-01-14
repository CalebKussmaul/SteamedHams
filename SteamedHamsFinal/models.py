from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from django.contrib.sessions.models import Session

# Create your models here.


class Submission(models.Model):
    id = models.AutoField(primary_key=True)
    frame = models.IntegerField(db_index=True)
    # path = 'frame{:04d}/{}.png'.format(frame, id)
    author = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    upvotes = models.IntegerField(default=0)
    downvotes = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    reports = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)

    def url(self):
        return 'https://steamedassets.nyc3.cdn.digitaloceanspaces.com/submissions/frame{:04d}/{}.png'.format(self.frame,
                                                                                                             self.id)

    def rank(self):
        for idx, sub in enumerate(Submission.objects.filter(frame=self.frame, deleted=False).order_by('-score')):
            if sub.id == self.id:
                return idx + 1
        return -1


class UserVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    is_upvote = models.BooleanField()
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, db_index=True)
    date = models.DateTimeField(auto_now_add=True)


def get_submission(frame, id):
    return Submission.objects.get(frame=frame, id=id)


class UserReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)


admin.site.register(Submission)
admin.site.register(UserReport)
admin.site.register(UserVote)
admin.site.register(Session)
