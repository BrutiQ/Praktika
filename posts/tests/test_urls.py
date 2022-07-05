from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, Group, User

SLUG = 'test-slug'
AUTHOR_NAME = 'pavel'
FOLLOWER_NAME = 'FAN'
NOT_AUTHOR_NAME = 'not_author'
LOGIN_URL = reverse('users:login')
LOGOUT_URL = reverse('users:logout')
MAIN_URL = reverse('posts:index')
FOLLOW_POSTS_URL = reverse('posts:follow_index')
GROUP_URL = reverse('posts:group_list', args=(SLUG,))
CREATE_POST_URL = reverse('posts:post_create')
UNEXISTING_URL = '/unexisting_page/'
PROFILE_URL = reverse('posts:profile', args=(AUTHOR_NAME,))
LOGIN_TO_CREATE_POST_URL = f'{LOGIN_URL}?next={CREATE_POST_URL}'
FOLLOW_URL = reverse('posts:profile_follow', args=(AUTHOR_NAME,))
UNFOLLOW_URL = reverse('posts:profile_unfollow', args=(AUTHOR_NAME,))
LOGIN_TO_FOLLOW_URL = f'{LOGIN_URL}?next={FOLLOW_URL}'
LOGIN_TO_UNFOLLOW_URL = f'{LOGIN_URL}?next={UNFOLLOW_URL}'
LOGIN_TO_FOLLOWS_URL = f'{LOGIN_URL}?next={FOLLOW_POSTS_URL}'


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=AUTHOR_NAME)
        cls.follower = User.objects.create_user(username=FOLLOWER_NAME)
        cls.not_author = User.objects.create_user(username=NOT_AUTHOR_NAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', args=(cls.post.id,))
        cls.EDIT_POST_URL = reverse('posts:post_edit', args=(cls.post.id,))
        cls.LOGIN_TO_EDIT_POST_URL = f'{LOGIN_URL}?next={cls.EDIT_POST_URL}'
        cls.guest = Client()
        cls.authorized = Client()
        cls.authorized.force_login(cls.author)
        cls.another = Client()
        cls.another.force_login(cls.not_author)
        cls.authorized_follower = Client()
        cls.authorized_follower.force_login(cls.follower)

    def test_exists_at_desired_location(self):
        """URL-адрес корректно открывает всем доступные страницы"""
        templates_url_names = {
            MAIN_URL: 'posts/index.html',
            GROUP_URL: 'posts/group_list.html',
            PROFILE_URL: 'posts/profile.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            self.EDIT_POST_URL: 'posts/create_post.html',
            CREATE_POST_URL: 'posts/create_post.html',
            FOLLOW_POSTS_URL: 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                self.assertTemplateUsed(
                    self.authorized.get(address), template)

    def test_urls_exists_at_desired_location(self):
        values = (
            (MAIN_URL, self.guest, 200),
            (MAIN_URL, self.authorized, 200),
            (GROUP_URL, self.guest, 200),
            (GROUP_URL, self.authorized, 200),
            (PROFILE_URL, self.guest, 200),
            (PROFILE_URL, self.authorized, 200),
            (self.POST_DETAIL_URL, self.guest, 200),
            (self.POST_DETAIL_URL, self.authorized, 200),
            (UNEXISTING_URL, self.guest, 404),
            (CREATE_POST_URL, self.authorized, 200),
            (CREATE_POST_URL, self.guest, 302),
            (self.EDIT_POST_URL, self.authorized, 200),
            (self.EDIT_POST_URL, self.guest, 302),
            (self.EDIT_POST_URL, self.another, 302),
            (FOLLOW_POSTS_URL, self.guest, 302),
            (FOLLOW_POSTS_URL, self.authorized, 200),
            (FOLLOW_URL, self.authorized_follower, 302),
            (UNFOLLOW_URL, self.authorized_follower, 302),
            (FOLLOW_URL, self.guest, 302),
            (UNFOLLOW_URL, self.guest, 302),
            (FOLLOW_URL, self.authorized, 302),
            (UNFOLLOW_URL, self.authorized, 404),
        )
        for url, client, exepected_code in values:
            with self.subTest(url=url, client=client):
                self.assertEqual(client.get(url).status_code, exepected_code)

    def test_pages_redirects(self):
        values = (
            (self.EDIT_POST_URL, self.guest, self.LOGIN_TO_EDIT_POST_URL),
            (self.EDIT_POST_URL, self.another, self.POST_DETAIL_URL),
            (CREATE_POST_URL, self.guest, LOGIN_TO_CREATE_POST_URL),
            (FOLLOW_URL, self.guest, LOGIN_TO_FOLLOW_URL),
            (UNFOLLOW_URL, self.guest, LOGIN_TO_UNFOLLOW_URL),
            (FOLLOW_URL, self.authorized_follower, PROFILE_URL),
            (UNFOLLOW_URL, self.authorized_follower, PROFILE_URL),
            (FOLLOW_POSTS_URL, self.guest, LOGIN_TO_FOLLOWS_URL),
            (FOLLOW_URL, self.authorized, PROFILE_URL),
        )
        for url, client, final_url in values:
            with self.subTest(url=url, client=client):
                self.assertRedirects(
                    client.get(url, follow=True), final_url)
