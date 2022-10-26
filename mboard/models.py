from django.db import models
from django.contrib.sessions.models import Session


class Post(models.Model):
    thread = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='post/images/', blank=True, verbose_name='Image')
    thumbnail = models.ImageField(upload_to='post/thumbnails/', blank=True)
    video = models.FileField(upload_to='post/videos/', blank=True)
    video_thumb = models.ImageField(upload_to='post/videos/thumbs', blank=True)
    bump = models.DateTimeField(auto_now=True)
    board = models.ForeignKey('Board', on_delete=models.CASCADE, null=False, blank=False)
    session = models.ForeignKey(Session, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        base_url = f'/{self.board}/thread'
        if self.thread is not None:
            return f'{base_url}/{self.thread.pk}/#id{self.pk}'
        return f'{base_url}/{self.pk}/'

    def posts_ids(self):
        ls = list(self.post_set.values_list('pk', flat=True))
        ls.append(int(self.pk))
        return ls


class Board(models.Model):
    board_link = models.CharField(max_length=5, unique=True, blank=False, null=False)
    board_title = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
        return self.board_link


class Rating(models.Model):
    user = models.ForeignKey(Session, on_delete=models.CASCADE, null=False, related_name='user')
    target = models.ForeignKey(Post, on_delete=models.CASCADE, null=False, related_name='target')
    vote = models.IntegerField(default=0)
    rank = models.FloatField(default=0)
    board = models.ForeignKey(Board, to_field='board_link', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['board', 'user', 'target'], name='unique_constraint')
        ]

    def __str__(self):
        return str(self.target)


class CalcTime(models.Model):
    user = models.ForeignKey(Session, on_delete=models.CASCADE)
    rank_calc_time = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    board = models.ForeignKey(Board, to_field='board_link', on_delete=models.CASCADE)

    def __str__(self):
        return str(self.user)
