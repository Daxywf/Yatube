import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


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
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.author = User.objects.create(username='test_profile')
        cls.author2 = User.objects.create(username='test_profile2')
        for i in range(1, 12):
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.post2 = Post.objects.create(
            text='test post2',
            author=PostsPagesTests.author2,
            group=PostsPagesTests.group2,
            image='posts/small.gif'
        )
        self.user = PostsPagesTests.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_home_page_paginator(self):
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(
            len(response.context['page_obj']),
            settings.PAG_VAL
        )

    def test_group_page_paginator(self):
        cache.clear()
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': PostsPagesTests.group.slug}
            )
        )
        self.assertEqual(
            len(response.context['page_obj']),
            settings.PAG_VAL
        )

    def test_profile_page_paginator(self):
        cache.clear()
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(
            len(response.context['page_obj']),
            settings.PAG_VAL
        )

    def test_pages_use_correct_template(self):
        templates_pages_names = {
            reverse(
                'posts:index'
            ): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': PostsPagesTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsPagesTests.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.author.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsPagesTests.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        pages = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': PostsPagesTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.author.username}
            ),
        ]
        for reverse_name in pages:
            cache.clear()
            response = self.authorized_client.get(reverse_name)
            self.assertIsInstance(
                response.context['page_obj'],
                Page
            )
        cache.clear()
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsPagesTests.post.id}
            )
        )
        self.assertIsInstance(
            response.context['post'],
            Post
        )

    def test_post_create_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsPagesTests.post.id}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_is_correct(self):
        def check_post_info(post):
            attributes = {
                post.text: self.post2.text,
                post.author: PostsPagesTests.author2,
                post.group: PostsPagesTests.group2,
                post.image: 'posts/small.gif',
            }
            for attribute, expected_value in attributes.items():
                with self.subTest(attribute=attribute):
                    self.assertEqual(attribute, expected_value)
            self.assertNotEqual(post.group, PostsPagesTests.group)

        pages = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': PostsPagesTests.group2.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.author2.username}
            ),
        ]
        for reverse_name in pages:
            cache.clear()
            response = self.authorized_client.get(reverse_name)
            post = response.context['page_obj'][0]
            check_post_info(post)
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post2.id}
            )
        )
        post = response.context['post']
        check_post_info(post)

    def test_index_cache(self):
        cache.clear()
        test_post = Post.objects.create(
            text='cache_test',
            group=PostsPagesTests.group,
            author=PostsPagesTests.author
        )
        response = self.authorized_client.get(
            reverse(
                'posts:index',
            )
        )
        first_post = response.context['page_obj'][0]
        self.assertEqual(test_post.text, first_post.text)
        self.assertEqual(test_post.author, first_post.author)
        self.assertEqual(test_post.group, first_post.group)
        test_post.delete()
        first_post = response.context['page_obj'][0]
        self.assertEqual(test_post.text, first_post.text)
        self.assertEqual(test_post.author, first_post.author)
        self.assertEqual(test_post.group, first_post.group)
        cache.clear()
        response = self.authorized_client.get(
            reverse(
                'posts:index',
            )
        )
        first_post = response.context['page_obj'][0]
        self.assertNotEqual(test_post.text, first_post.text)
        self.assertNotEqual(test_post.author, first_post.author)
        self.assertNotEqual(test_post.group, first_post.group)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.user1 = User.objects.create(username='user1')
        cls.user2 = User.objects.create(username='user2')
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.author
        )
        cls.follow = Follow.objects.create(
            user=FollowTests.user1,
            author=FollowTests.author
        )

    def setUp(self):
        self.user1 = FollowTests.user1
        self.user2 = FollowTests.user2
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_follow(self):
        self.authorized_client2.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': FollowTests.author}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=FollowTests.user2,
                author=FollowTests.author
            ).exists()
        )

    def test_unfollow(self):
        self.authorized_client1.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': FollowTests.author}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=FollowTests.user1,
                author=FollowTests.author
            ).exists()
        )

    def test_post_appearance(self):
        response = self.authorized_client1.get(
            reverse('posts:follow_index')
        )
        self.assertTrue(
            FollowTests.post in response.context['page_obj']
        )
        response = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        self.assertFalse(
            FollowTests.post in response.context['page_obj']
        )
