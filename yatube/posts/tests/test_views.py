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
FOLLOW_INDEX_URL = reverse('posts:follow_index')
PROFILE_URL1 = reverse(
    'posts:profile',
    kwargs={'username': 'test_profile'}
)
PROFILE_URL2 = reverse(
    'posts:profile',
    kwargs={'username': 'test_profile2'}
)
GROUP_URL1 = reverse(
    'posts:group_posts',
    kwargs={'slug': 'test-slug'}
)
GROUP_URL2 = reverse(
    'posts:group_posts',
    kwargs={'slug': 'wrong-group'}
)
FOLLOW_URL = reverse(
    'posts:profile_follow',
    kwargs={'username': 'test_profile2'}
)
UNFOLLOW_URL = reverse(
    'posts:profile_unfollow',
    kwargs={'username': 'test_profile2'}
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='test-description'
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
        cls.author2 = User.objects.create(
            username='test_profile2',
            first_name='test_1st_name',
            last_name='test_last_name'
        )
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
        cls.follow = Follow.objects.create(
            user=cls.author,
            author=cls.author2
        )
        cls.user2 = User.objects.create(username='user2')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.post = Post.objects.create(
            text='text',
            author=self.author2,
            group=self.group2,
            image=self.uploaded
        )

        self.POST_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.author2)
        self.user_client = Client()
        self.user_client.force_login(self.user2)
        cache.clear()

    def test_pages_paginator(self):
        responses = [
            PROFILE_URL1,
            GROUP_URL1,
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
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group, self.post.group)
            self.assertEqual(post.image, self.post.image)

        pages = [
            INDEX_URL,
            GROUP_URL2,
            PROFILE_URL2,
            FOLLOW_INDEX_URL
        ]
        for reverse_name in pages:
            response = self.authorized_client.get(reverse_name)
            post = Post.objects.get(id=self.post.id)
            self.assertIn(post, response.context['page_obj'])
            check_post_info(post)
        response = self.authorized_client.get(self.POST_URL)
        post = response.context['post']
        check_post_info(post)

    def test_index_cache(self):
        first_content = self.authorized_client.get(
            INDEX_URL
        ).content
        self.post.delete()
        content_after_deleting = self.authorized_client.get(
            INDEX_URL
        ).content
        cache.clear()
        content_after_cleaning = self.authorized_client.get(
            INDEX_URL
        ).content
        self.assertEqual(first_content, content_after_deleting)
        self.assertNotEqual(first_content, content_after_cleaning)

    def test_post_not_exists_on_wrong_group_page(self):
        response = self.authorized_client.get(GROUP_URL1)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_post_on_group_page_has_correct_group(self):
        response = self.authorized_client.get(GROUP_URL1)
        group = response.context['group']
        self.assertEqual(group.id, self.group.id)
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)
        self.assertEqual(group.description, self.group.description)

    def test_post_on_profile_page_has_correct_author(self):
        response = self.authorized_client.get(PROFILE_URL2)
        author = response.context['author']
        self.assertEqual(author.id, self.author2.id)
        self.assertEqual(author.username, self.author2.username)
        self.assertEqual(author.first_name, self.author2.first_name)
        self.assertEqual(author.last_name, self.author2.last_name)

    def test_follow(self):
        self.user_client.get(FOLLOW_URL)
        self.assertTrue(
            Follow.objects.filter(
                user=self.user2,
                author=self.author2
            ).exists()
        )

    def test_unfollow(self):
        self.authorized_client.get(UNFOLLOW_URL)
        self.assertFalse(
            Follow.objects.filter(
                user=self.author,
                author=self.author2
            ).exists()
        )

    def test_post_not_exists_on_other_follow_index(self):
        response = self.authorized_client2.get(
            FOLLOW_INDEX_URL
        )
        self.assertNotIn(
            self.post, response.context['page_obj']
        )
