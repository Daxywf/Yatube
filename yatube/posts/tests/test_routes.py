from django.test import TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostsRoutesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            username='user1'
        )
        cls.group = Group.objects.create(
            title='group1',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )

    def test_reverse_url_equal_to_usual(self):
        urls = {
            '/': reverse('posts:index'),
            '/follow/': reverse('posts:follow_index'),
            f'/profile/{self.user.username}/': reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ),
            f'/group/{self.group.slug}/': reverse(
                'posts:group_posts',
                kwargs={'slug': self.group.slug}
            ),
            f'/posts/{self.post.id}/': reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ),
            '/create/': reverse('posts:post_create'),
            f'/posts/{self.post.id}/edit/': reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            f'/profile/{self.user.username}/follow/': reverse(
                'posts:profile_follow',
                kwargs={'username': self.user.username}
            ),
            f'/profile/{self.user.username}/unfollow/': reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user.username}
            )
        }
        for url, reverse_result in urls.items():
            with self.subTest(url=url):
                self.assertEqual(url, reverse_result)
