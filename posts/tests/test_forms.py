import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post, User

USERNAME = 'pavel'
NOT_AUTHOR_NAME = 'not_author'
CREATE_POST_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile', args=(USERNAME,))
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
LOGIN_URL = reverse('users:login')
LOGIN_TO_CREATE_POST_URL = f'{LOGIN_URL}?next={CREATE_POST_URL}'
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.not_author = User.objects.create_user(username=NOT_AUTHOR_NAME)
        cls.old_group = Group.objects.create(
            title='Старая тестовая группа',
            slug='test-slug-old',
            description='Тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='Новая тестовая группа',
            slug='test-slug-new',
            description='Тестовое описание',
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.form = PostForm()
        cls.guest = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.another = Client()
        cls.another.force_login(cls.not_author)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.old_group,
        )
        cls.ADD_COMMENT_URL = reverse(
            'posts:add_comment', args=(cls.post.id,))
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', args=(cls.post.id,))
        cls.EDIT_POST_URL = reverse('posts:post_edit', args=(cls.post.id,))
        cls.LOGIN_TO_EDIT_POST_URL = f'{LOGIN_URL}?next={cls.EDIT_POST_URL}'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_comment(self):
        """Валидная форма создает коммент"""
        comment_count = Comment.objects.count()
        self.assertEqual(comment_count, 0)
        form_data = {'text': 'Тестовый текст'}
        response = self.authorized_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        comment = Comment.objects.get()
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)

    def test_create_and_edit_page_show_correct_context(self):
        """Шаблон create и edit сформированы с правильным контекстом."""
        page_names = {
            self.EDIT_POST_URL,
            CREATE_POST_URL,
        }
        for url_name in page_names:
            response = self.authorized_client.get(url_name)
            for value, expected in self.form_fields.items():
                with self.subTest(value=value):
                    self.assertIsInstance(
                        response.context.get(
                            'form').fields.get(value), expected)

    def test_post_edit(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        self.assertEqual(posts_count, 1)
        posts_count = Post.objects.count()
        uploaded_edited = SimpleUploadedFile(
            name='small_1.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый измененный текст',
            'group': self.new_group.id,
            'image': uploaded_edited,
        }
        response = self.authorized_client.post(
            self.EDIT_POST_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        post = response.context.get('post')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertIn(form_data['image'].name, post.image.name)
        self.assertRedirects(response, self.POST_DETAIL_URL)

    def test_not_author_edit_post(self):
        """Проверка, что не автор не может редактировать пост"""
        clients = [
            self.guest,
            self.another,
        ]
        uploaded_edited = SimpleUploadedFile(
            name='small_1.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Измененный текст',
            'group': self.new_group.id,
            'image': uploaded_edited,
        }
        response = self.guest.post(
            self.EDIT_POST_URL,
            data=form_data,
        )
        for client in clients:
            with self.subTest(client=client):
                post = Post.objects.get(pk=self.post.id)
                self.assertRedirects(response, self.LOGIN_TO_EDIT_POST_URL)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.image, self.post.image)
                self.assertEqual(post.author, self.post.author)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.old_group = Group.objects.create(
            title='Старая тестовая группа',
            slug='test-slug-old',
            description='Тестовое описание',
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.form = PostForm()
        cls.guest = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        self.assertEqual(posts_count, 0)
        form_data = {
            'text': 'Тестовый текст',
            'group': self.old_group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            CREATE_POST_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, PROFILE_URL)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.get()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertIn(form_data['image'].name, post.image.name)

    def test_guest_creation_post(self):
        """Проверка, что гость не может создать пост"""
        self.assertEqual(Post.objects.count(), 0)
        form_data = {
            'text': 'Тестовый текст',
            'group': self.old_group.id,
            'image': self.uploaded,
        }
        response = self.guest.post(
            CREATE_POST_URL,
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, LOGIN_TO_CREATE_POST_URL)
        self.assertEqual(Post.objects.count(), 0)
