from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug'
        )
        cls.author = User.objects.create(
            username='test_profile'
        )
        cls.not_author = User.objects.create(
            username='test_profile2'
        )
        cls.post = Post.objects.create(
            text='test text',
            author=User.objects.get(username='test_profile')
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostsURLTests.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.not_author = Client()
        self.not_author.force_login(PostsURLTests.not_author)

    def test_page_responses(self):
        page_status_codes = {
            HTTPStatus.OK: '/',
            HTTPStatus.OK: f'/group/{PostsURLTests.group.slug}/',
            HTTPStatus.OK: f'/posts/{PostsURLTests.post.id}/',
            HTTPStatus.OK: f'/profile/{PostsURLTests.author.username}/',
            HTTPStatus.NOT_FOUND: '/unexisting_page/',
        }
        for status, adress in page_status_codes.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            '/': 'posts/index.html',
            f'/profile/{PostsURLTests.author.username}/': 'posts/profile.html',
            f'/group/{PostsURLTests.group.slug}/': 'posts/group_list.html',
            f'/posts/{PostsURLTests.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{PostsURLTests.post.id}/edit/': 'posts/create_post.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_create_url_redirect_anonymous_on_login(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_url_redirect_anonymous_on_login(self):
        response = self.guest_client.get(
            f'/posts/{PostsURLTests.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{PostsURLTests.post.id}/edit/'
        )

    def test_post_edit_url_reqirect_non_author_on_login(self):
        response = self.not_author.get(
            f'/posts/{PostsURLTests.post.id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response, f'/posts/{PostsURLTests.post.id}/'
        )
