from django.test import TestCase, Client
from mboard.models import Post, Board
from mboard.forms import PostForm, ThreadPostForm
from django.core.files.uploadedfile import SimpleUploadedFile
from captcha.conf import settings


class CreateThread(TestCase):
    def setUp(self):
        self.c = Client()
        Board.objects.create(board_title='test', board_link='t')
        self.thread = Post.objects.create(board_id=Board.objects.get(board_link='t').pk)
        settings.CAPTCHA_TEST_MODE = True
        self.data = {'text': 'what did he mean by this?',
                     'poster': 'literally who?',
                     'captcha_0': 'passed',
                     'captcha_1': 'passed'}
        self.files = ['mboard/tests/testwebm.webm', 'mboard/tests/testimage.jpg']

    def test_form_is_valid(self):
        for file in self.files:
            with open(file, 'rb') as f:
                form = PostForm(data=self.data, files={'file': SimpleUploadedFile('filename', f.read(),
                                                                                  content_type='video')})
                f.seek(0)
                thread_form = ThreadPostForm(data=self.data, files={'file': SimpleUploadedFile('filename', f.read(),
                                                                                               content_type='video')})
                assert form.is_valid()
                assert thread_form.is_valid()

    def test_submit_form_returns_200(self):
        urls = [
            f'/{self.thread.board.board_link}/thread/{self.thread.pk}/',  # submit from a thread
            f'/{self.thread.board}/',  # submit from a board page
            '/posting/'  # ajax posting
        ]
        for url in urls:
            response = self.c.post(url, {'text': 'dfsklfds'})
            self.assertEqual(response.status_code, 200)

    def test_return_404(self):
        not_existing_urls = ['/nonexistingboard/', '/t/wtf/', '/t/thread/31231/', '/t/thread/t', '/a/']
        for url in not_existing_urls:
            response = self.c.get(url)
            self.assertEqual(response.status_code, 404)
        self.assertEqual(self.c.get('/t/313/').status_code, 302)  # invalid page number

    def test_return_200(self):
        urls = ['/t/', f'/t/thread/{self.thread.pk}/', '/t/1/']
        for url in urls:
            self.assertEqual(self.c.get(url).status_code, 200)

    def test_prevent_thread_creation_without_image(self):
        form = ThreadPostForm(data=self.data)
        self.assertFalse(form.is_valid())

    def test_if_post_has_image_text_not_required(self):
        with open(self.files[1], 'rb') as f:
            form = PostForm(data={'captcha_0': 'passed', 'captcha_1': 'passed'},
                            files={'file': SimpleUploadedFile('img', f.read(), content_type='image')})
            self.assertTrue(form.is_valid())
