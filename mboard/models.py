from django.db import models


class Post(models.Model):
    thread = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    poster = models.CharField(max_length=35, default='Anon')
    text = models.TextField()
    date = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='post/images/', blank=True, verbose_name='Image')
    thumbnail = models.ImageField(upload_to='post/thumbnails/', blank=True)
    video = models.FileField(upload_to='post/videos/', blank=True)
    video_thumb = models.ImageField(upload_to='post/videos/thumbs', blank=True)
    bump = models.DateTimeField(auto_now=True)
    board = models.ForeignKey('Board', on_delete=models.CASCADE, null=False, blank=False)

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        if self.thread is None:
            return f'/{self.board}/thread/{self.pk}/'
        else:
            return f'/{self.board}/thread/{self.thread.pk}/#id{self.pk}'

    def posts_ids(self):
        ls = list(self.post_set.values_list('pk', flat=True))
        ls.append(int(self.pk))
        return ls


class Board(models.Model):
    board_link = models.CharField(max_length=5, blank=False, null=False)
    board_title = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
        return self.board_link
