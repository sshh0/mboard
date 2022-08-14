from django import forms
from django.core.exceptions import ValidationError
from mboard.models import Post, Board
from captcha.fields import CaptchaField


class PostForm(forms.ModelForm):
    text = forms.CharField(error_messages={'required': 'Enter the message'},
                           min_length=1, widget=forms.Textarea(attrs={'cols': 53}))
    poster = forms.CharField(required=False, empty_value='Anon', widget=forms.TextInput(attrs={'placeholder': 'Anon'}))
    threadnum = forms.IntegerField(required=False)
    image = forms.ImageField(required=False)
    # board = forms.ModelChoiceField(queryset=Board.objects.all(), widget=forms.HiddenInput, to_field_name='board_name')
    captcha = CaptchaField()

    def clean_image(self):
        image = self.cleaned_data['image']
        if image:
            if image.size > 1 * 1024 * 1024:
                raise ValidationError('> 1 MB')
            return image
    #
    # def clean_board(self):
    #     print(self)
    #     return self.cleaned_data['board']

    class Meta:
        model = Post
        fields = ['poster', 'text', 'threadnum', 'image']  # 'board'


class ThreadPostForm(PostForm):
    image = forms.ImageField(required=True)
