from django import forms
from mboard.models import Post
from captcha.fields import CaptchaField
import subprocess
from magic import from_buffer
from django.core.files.base import ContentFile
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from pathlib import Path


class PostForm(forms.ModelForm):
    text = forms.CharField(error_messages={'required': 'Enter the message'}, min_length=1, widget=forms.Textarea())
    poster = forms.CharField(required=False, empty_value='Анон', widget=forms.TextInput(attrs={'placeholder': 'Анон'}))
    threadnum = forms.IntegerField(required=False)
    captcha = CaptchaField()
    file = forms.FileField(required=False)

    class Meta:
        model = Post
        fields = ['poster', 'text', 'threadnum']

    def clean_file(self):
        if self.cleaned_data['file']:
            file = self.cleaned_data['file']
            mime_type = from_buffer(file.read(), mime=True)
            if 'image' in mime_type:
                if file.size > 1 * 1024 * 1024:
                    self.add_error('file', 'Картинка > 1 MB')
                self.instance.image = self.files['file']
                self.instance.thumbnail = make_thumbnail(self.files['file'])
            elif 'video' in mime_type:
                if 'webm' in mime_type or 'mp4' in mime_type:
                    if file.size > 5 * 1024 * 1024:
                        self.add_error('file', 'Видео > 5 MB')
                    args = ['ffmpeg', '-i', 'pipe:0', '-ss', '00:00:01', '-vf', 'scale=150:120',
                            '-vframes', '1', '-f', 'image2pipe', '-c', 'mjpeg', 'pipe:1', '-loglevel', 'quiet']
                    file.seek(0)
                    process = subprocess.run(args, input=file.read(), stdout=subprocess.PIPE)
                    if process.returncode != 0:
                        self.add_error('file', 'Ошибка загрузки')
                    self.instance.video = self.files['file']
                    self.instance.video_thumb = ContentFile(content=process.stdout, name=Path(file.name).stem+'.jpg')
                else:
                    self.add_error('file', 'Только Webm/mp4')
            else:
                self.add_error('file', 'Только изображения и webm/mp4')


class ThreadPostForm(PostForm):
    file = forms.FileField(required=True)


def make_thumbnail(inmemory_image):
    image = Image.open(inmemory_image)
    image.thumbnail(size=(200, 220))
    output = BytesIO()
    image.save(output, quality=85, format=image.format)
    thumb = InMemoryUploadedFile(
        output, 'ImageField', 'thumb_' + inmemory_image.name, 'image/jpeg', None, None)
    return thumb
