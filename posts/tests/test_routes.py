from django.test import TestCase
from django.urls import reverse

from posts.urls import app_name

POST_ID = 1
SLUG = 'test-slug'
USERNAME = 'pavel'


class PostURLTests(TestCase):
    def test_exists_at_desired_location(self):
        values = (
            ('/', 'index', ()),
            (f'/group/{SLUG}/', 'group_list', (SLUG,)),
            (f'/profile/{USERNAME}/', 'profile', (USERNAME,)),
            (f'/posts/{POST_ID}/', 'post_detail', (POST_ID,)),
            (f'/posts/{POST_ID}/edit/', 'post_edit', (POST_ID,)),
            ('/create/', 'post_create', ()),
            (f'/posts/{POST_ID}/comment/', 'add_comment', (POST_ID,)),
            ('/follow/', 'follow_index', ()),
            (f'/profile/{USERNAME}/follow/', 'profile_follow', (USERNAME,)),
            (f'/profile/{USERNAME}/unfollow/',
             'profile_unfollow', (USERNAME,)),
        )
        for address, url, args in values:
            with self.subTest(address=address):
                self.assertEqual(address, reverse(
                    f'{app_name}:{url}', args=args))
