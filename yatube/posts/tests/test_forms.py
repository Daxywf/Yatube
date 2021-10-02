import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)
CREATE_URL = reverse('posts:post_create')


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
        cls.post = Post.objects.create(
            text='Текст',
            group=cls.group,
            author=cls.user
        )
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок2',
            slug='test-slug2'
        )
        cls.EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )
        cls.POST_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile',
            kwargs={'username': cls.user.username}
        )
        cls.ADD_COMMENT_URL = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post.id}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        id_list1 = list(Post.objects.values_list('pk', flat=True))
        posts_count = len(id_list1)
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            CREATE_URL,
            data=form_data,
            follow=True
        )
        id_list2 = list(Post.objects.values_list('pk', flat=True))
        new_posts_count = len(id_list2)
        self.assertRedirects(
            response,
            self.PROFILE_URL
        )
        self.assertEqual(len(set(id_list2) - set(id_list1)), 1)
        post = Post.objects.filter(
            pk__in=id_list2
        ).exclude(pk__in=id_list1)[0]
        self.assertEqual(new_posts_count, posts_count + 1)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_edit_post(self):
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый текст',
            'group': self.group2.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            self.EDIT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            self.POST_URL
        )
        post = response.context['post']
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.image, 'posts/small2.gif')
        new_posts_count = Post.objects.count()
        self.assertEqual(posts_count, new_posts_count)

    def test_anonymous_post_create(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Анонимный текст',
            'group': self.group.id
        }
        self.guest_client.post(
            CREATE_URL,
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_anonymous_post_edit(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Анонимный новый текст',
            'group': self.group2.id
        }
        self.guest_client.post(
            self.EDIT_URL,
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.id)
        new_posts_count = Post.objects.count()
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(posts_count, new_posts_count)

    def test_anonymous_add_comment(self):
        comments_count = self.post.comments.count()
        form_data = {
            'text': 'Анонимный комментарий'
        }
        self.guest_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True
        )
        new_comments_count = self.post.comments.count()
        self.assertEqual(comments_count, new_comments_count)

    def test_add_comment(self):
        comments_count = self.post.comments.count()
        form_data = {
            'text': 'Комментарий'
        }
        self.authorized_client.post(
            self.ADD_COMMENT_URL,
            data=form_data,
            follow=True
        )
        new_comments_count = self.post.comments.count()
        self.assertEqual(comments_count + 1, new_comments_count)
        comment = self.post.comments.filter(
            author=self.user
        )[0]
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)

    def test_post_create_and_edit_pages_show_correct_context(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                reverse_names = [
                    CREATE_URL,
                    self.EDIT_URL
                ]
                for reverse_name in reverse_names:
                    response = self.authorized_client.get(reverse_name)
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)
