import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post, User
from yatube.settings import POSTS_PER_PAGE

SLUG_GROUP = 'test-slug'
AUTHOR_NAME = 'pavel'
FOLLOWER_NAME = 'FAN'
SLUG_ANOTHER_GROUP = 'test-test'
MAIN_URL = reverse('posts:index')
FOLLOW_POSTS_URL = reverse('posts:follow_index')
SECOND_PAGE_MAIN_URL = f'{MAIN_URL}?page=2'
GROUP_URL = reverse('posts:group_list', args=(SLUG_GROUP,))
ANOTHER_GROUP_URL = reverse(
    'posts:group_list', args=(SLUG_ANOTHER_GROUP,))
CREATE_POST_URL = reverse('posts:post_create')
REMAINING_POSTS = 4
NUMBER_OF_TEST_POSTS = POSTS_PER_PAGE + REMAINING_POSTS
PROFILE_URL = reverse('posts:profile', args=(AUTHOR_NAME,))
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
FOLLOW_URL = reverse('posts:profile_follow', args=(AUTHOR_NAME,))
UNFOLLOW_URL = reverse('posts:profile_unfollow', args=(AUTHOR_NAME,))
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR_NAME)
        cls.follower = User.objects.create_user(username=FOLLOWER_NAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG_GROUP,
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            slug=SLUG_ANOTHER_GROUP,
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.follow = Follow.objects.create(
            author=cls.author,
            user=cls.follower,
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.authorized_follower = Client()
        cls.authorized_follower.force_login(cls.follower)
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', args=(cls.post.id,))
        cls.EDIT_POST_URL = reverse('posts:post_edit', args=(cls.post.id,))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        url_names = [
            MAIN_URL,
            GROUP_URL,
            PROFILE_URL,
            self.POST_DETAIL_URL,
            FOLLOW_POSTS_URL,
        ]
        for url in url_names:
            with self.subTest(url=url):
                if url == FOLLOW_POSTS_URL:
                    response = self.authorized_follower.get(url)
                else:
                    response = self.authorized_client.get(url)
                if url == self.POST_DETAIL_URL:
                    post = response.context.get('post')
                else:
                    self.assertEqual(
                        len(response.context['page_obj']), 1)
                    post = response.context['page_obj'][0]
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.id, self.post.id)
                self.assertEqual(post.image, self.post.image)

    def test_author_in_profile_context(self):
        response = self.authorized_client.get(PROFILE_URL)
        user = response.context.get('author')
        self.assertEqual(user, self.author)

    def test_group_in_group_list_context(self):
        response = self.authorized_client.get(GROUP_URL)
        group = response.context.get('group')
        self.assertEqual(group, self.group)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)

    def test_objects_not_in_another_places(self):
        url_names = [
            ANOTHER_GROUP_URL,
            FOLLOW_POSTS_URL,
        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertNotIn(self.post, response.context["page_obj"])

    def test_login_user_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей
        """
        self.follow.delete()
        self.authorized_follower.get(FOLLOW_URL)
        follow = Follow.objects.filter(
            user=self.follower,
            author=self.author,
        ).exists()
        self.assertTrue(follow)

    def test_login_user_unfollow(self):
        """Авторизованный пользователь может
        отписываться от других пользователей
        """
        self.authorized_follower.get(UNFOLLOW_URL)
        follow = Follow.objects.filter(
            user=self.follower,
            author=self.author,
        ).exists()
        self.assertFalse(follow)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR_NAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG_GROUP,
            description='Тестовое описание',
        )
        cls.post = Post.objects.bulk_create([
            Post(
                author=cls.author,
                group=cls.group,
            )
            for i in range(NUMBER_OF_TEST_POSTS)
        ])
        cls.authorized = Client()
        cls.authorized.force_login(cls.author)

    def test_pages_contains_nessesary_records(self):
        """На страницах нужное кол-во постов."""
        values = {
            (MAIN_URL, POSTS_PER_PAGE),
            (SECOND_PAGE_MAIN_URL, REMAINING_POSTS),
        }
        for address, number in values:
            with self.subTest(address=address):
                self.assertEqual(len(
                    self.authorized.get(address).context['page_obj']), number)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR_NAME)
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)

    def test_cache_in_index(self):
        """Проверка работы кэша на главной странице"""
        non_cleared_cache = self.authorized_client.get(MAIN_URL).content
        self.post.delete()
        post_before_clearing_cache = self.authorized_client.get(
            MAIN_URL).content
        self.assertEqual(non_cleared_cache, post_before_clearing_cache)
        cache.clear()
        cleared_cache = self.authorized_client.get(MAIN_URL).content
        self.assertNotEqual(non_cleared_cache, cleared_cache)
