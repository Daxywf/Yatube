from django.test import TestCase
from django.urls import reverse

POST_ID = 1
USERNAME = 'user1'
GROUP_SLUG = 'test_slug'


class PostsRoutesTests(TestCase):
    def test_reverse_url_equal_to_usual(self):
        urls = [
            ['/', 'posts:index', {}],
            ['/create/', 'posts:post_create', {}],
            [f'/profile/{USERNAME}/', 'posts:profile',
             {'username': USERNAME}],
            [f'/group/{GROUP_SLUG}/', 'posts:group_posts',
             {'slug': GROUP_SLUG}],
            [f'/posts/{POST_ID}/', 'posts:post_detail',
             {'post_id': POST_ID}],
            [f'/posts/{POST_ID}/edit/', 'posts:post_edit',
             {'post_id': POST_ID}],
            [f'/profile/{USERNAME}/follow/', 'posts:profile_follow',
             {'username': USERNAME}],
            [f'/profile/{USERNAME}/unfollow/', 'posts:profile_unfollow',
             {'username': USERNAME}],
        ]
        for url, reverse_name, kwargs in urls:
            with self.subTest(url=url):
                self.assertEqual(url, reverse(reverse_name, kwargs=kwargs))
