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


class PostForm(forms.ModelForm):  # fields defined declaratively do not draw their
    file = forms.FileField(required=False)  # attributes like max_length or required from the corresponding model
    text = forms.CharField(error_messages={'required': 'Введите сообщение'}, required=False, max_length=4000,
                           widget=forms.Textarea())
    poster = forms.CharField(required=False, empty_value='Анон', widget=forms.TextInput(attrs={'placeholder': 'Анон'}))
    thread_id = forms.IntegerField(required=False)
    captcha = CaptchaField(error_messages={'invalid': 'Капча введена неверно'})

    class Meta:
        model = Post
        fields = ['poster', 'text', 'thread_id']

    def clean(self):
        # "By the time the form’s clean() method is called, all the individual field clean methods will have been run"
        cleaned_data = super().clean()
        if not cleaned_data.get('file') and not cleaned_data.get('text'):  # with get no error raised if no such field
            raise forms.ValidationError('Заполните форму')
        return self.cleaned_data

    def clean_file(self):
        if self.cleaned_data['file']:
            file = self.cleaned_data['file']
            mime_type = from_buffer(file.read(), mime=True)
            if 'image' in mime_type:
                if file.size > 1 * 1024 * 1024:
                    raise forms.ValidationError('Картинка > 1 MB')
                self.instance.image = self.files['file']
                self.instance.thumbnail = make_thumbnail(self.files['file'])
            elif 'video' in mime_type:
                if 'webm' in mime_type or 'mp4' in mime_type:
                    if file.size > 5 * 1024 * 1024:
                        raise forms.ValidationError('file', 'Видео > 5 MB')
                    args = ['ffmpeg', '-i', 'pipe:0', '-ss', '00:00:01', '-vf', 'scale=150:120',
                            '-vframes', '1', '-f', 'image2pipe', '-c', 'mjpeg', 'pipe:1', '-loglevel', 'quiet']
                    file.seek(0)
                    process = subprocess.run(args, input=file.read(), stdout=subprocess.PIPE)
                    if process.returncode != 0:
                        raise forms.ValidationError('Ошибка загрузки')
                    self.instance.video = self.files['file']
                    self.instance.video_thumb = ContentFile(content=process.stdout, name=Path(file.name).stem + '.jpg')
                else:
                    raise forms.ValidationError('Только Webm/mp4')
            else:
                raise forms.ValidationError('Только изображения и webm/mp4')
            return file  # "Always return a value to use as the new cleaned data, even if this method didn't change it"


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
