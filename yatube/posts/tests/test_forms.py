import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug'
        )
        cls.user = User.objects.create(
            username='test_profile'
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.post = Post.objects.create(
            text='Текст',
            group=PostCreateFormTests.group,
            author=PostCreateFormTests.user
        )
        self.group2 = Group.objects.create(
            title='Тестовый заголовок2',
            slug='test-slug2'
        )
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}))
        post = Post.objects.latest('pub_date')
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, PostCreateFormTests.group)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_edit_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый текст',
            'group': PostCreateFormTests.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        post = Post.objects.get(id=self.post.id)
        self.assertNotEqual(post.text, self.post.text)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, PostCreateFormTests.group)
        self.assertEqual(post.image, 'posts/small2.gif')
        new_posts_count = Post.objects.count()
        self.assertEqual(posts_count, new_posts_count)

    def test_anonymous_post_create(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Уникальный анонимный текст',
            'group': PostCreateFormTests.group.id
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                group=PostCreateFormTests.group
            ).exists()
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_anonymous_post_edit(self):
        form_data = {
            'text': 'Анонимный новый текст',
            'group': self.group2.id
        }
        self.guest_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertNotEqual(post.text, form_data['text'])
        self.assertNotEqual(post.group, form_data['group'])

    def test_anonymous_add_comment(self):
        comments_count = self.post.comments.count()
        form_data = {
            'text': 'Анонимный комментарий'
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        new_comments_count = self.post.comments.count()
        self.assertEqual(comments_count, new_comments_count)
        self.assertFalse(
            self.post.comments.filter(
                text=form_data['text']
            ).exists()
        )

    def test_add_comment(self):
        comments_count = self.post.comments.count()
        form_data = {
            'text': 'Комментарий'
        }
        self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        new_comments_count = self.post.comments.count()
        self.assertEqual(comments_count + 1, new_comments_count)
        self.assertTrue(
            self.post.comments.filter(
                text=form_data['text']
            ).exists()
        )
