import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
INDEX_URL = reverse('posts:index')
FOLLOW_URL = reverse('posts:follow_index')
FOLLOW_INDEX_URL = reverse('posts:follow_index')


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug'
        )

        cls.group2 = Group.objects.create(
            title='Тестовый заголовок2',
            slug='wrong-group'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.author = User.objects.create(username='test_profile')
        cls.author2 = User.objects.create(username='test_profile2')
        for i in range(1, settings.PAGINATION_VALUE + 1):
            Post.objects.create(
                text=f'test text{i}',
                author=cls.author,
                group=cls.group
            )
        cls.post = Post.objects.create(
            text='test post1',
            author=cls.author,
            group=cls.group
        )
        cls.post2 = Post.objects.create(
            text='test post2',
            author=cls.author2,
            group=cls.group2,
            image=cls.uploaded
        )
        cls.follow = Follow.objects.create(
            user=cls.author,
            author=cls.author2
        )
        cls.user2 = User.objects.create(username='user2')
        cls.PROFILE_URL1 = reverse(
            'posts:profile',
            kwargs={'username': cls.author.username}
        )
        cls.PROFILE_URL2 = reverse(
            'posts:profile',
            kwargs={'username': cls.author2.username}
        )
        cls.GROUP_URL1 = reverse(
            'posts:group_posts',
            kwargs={'slug': cls.group.slug}
        )
        cls.GROUP_URL2 = reverse(
            'posts:group_posts',
            kwargs={'slug': cls.group2.slug}
        )
        cls.POST_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post2.id}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.author2)
        self.user_client = Client()
        self.user_client.force_login(self.user2)
        cache.clear()

    def test_pages_paginator(self):
        responses = [
            self.PROFILE_URL1,
            self.GROUP_URL1,
            INDEX_URL,
        ]
        for reverse_name in responses:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.PAGINATION_VALUE
                )

    def test_correct_post_appears_on_pages(self):
        def check_post_info(post):
            self.assertEqual(post.text, self.post2.text)
            self.assertEqual(post.author, self.post2.author)
            self.assertEqual(post.group, self.post2.group)
            self.assertEqual(post.image, self.post2.image)

        pages = [
            INDEX_URL,
            self.GROUP_URL2,
            self.PROFILE_URL2,
            FOLLOW_INDEX_URL
        ]
        for reverse_name in pages:
            response = self.authorized_client.get(reverse_name)
            post = response.context['page_obj'][0]
            check_post_info(post)
        response = self.authorized_client.get(self.POST_URL)
        post = response.context['post']
        check_post_info(post)

    def test_index_cache(self):
        response = self.authorized_client.get(INDEX_URL)
        first_content = response.content
        response.context['page_obj'][0].delete()
        response = self.authorized_client.get(INDEX_URL)
        content_after_deleting = response.content
        cache.clear()
        response = self.authorized_client.get(INDEX_URL)
        content_after_cleaning = response.content
        self.assertEqual(first_content, content_after_deleting)
        self.assertNotEqual(first_content, content_after_cleaning)

    def test_post_not_exists_on_wrong_group_page(self):
        response = self.authorized_client.get(self.GROUP_URL1)
        self.assertNotIn(self.post2, response.context['page_obj'])

    def test_post_on_group_page_has_correct_group(self):
        response = self.authorized_client.get(self.GROUP_URL2)
        group_post = response.context['page_obj'][0]
        self.assertEqual(group_post.group, self.group2)

    def test_post_on_profile_page_has_correct_author(self):
        response = self.authorized_client.get(self.PROFILE_URL2)
        profile_post = response.context['page_obj'][0]
        self.assertEqual(profile_post.author, self.author2)

    def test_follow(self):
        self.user_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author2.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user2,
                author=self.author2
            ).exists()
        )

    def test_unfollow(self):
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author2.username}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.author,
                author=self.author2
            ).exists()
        )

    def test_post_appearance(self):
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(
            self.post2, response.context['page_obj']
        )
        self.assertEqual(self.post2.author, self.author2)

    def test_post_not_exists_on_other_follow_index(self):
        response = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(
            self.post, response.context['page_obj']
        )
