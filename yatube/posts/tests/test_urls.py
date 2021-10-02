from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

INDEX_URL = reverse('posts:index')
FOLLOW_URL = reverse('posts:follow_index')
CREATE_URL = reverse('posts:post_create')
UNEXISTING_URL = '/unexisting_page/'


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
        cls.not_author1 = User.objects.create(
            username='test_profile2'
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.author
        )
        cls.PROFILE_URL = reverse(
            'posts:profile',
            kwargs={'username': cls.author.username}
        )
        cls.GROUP_URL = reverse(
            'posts:group_posts',
            kwargs={'slug': cls.group.slug}
        )
        cls.POST_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )
        cls.POSTS_EDIT_URL = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.id}
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.not_author = Client()
        self.not_author.force_login(self.not_author1)

    def test_guest_responses(self):
        page_status_codes = {
            INDEX_URL: HTTPStatus.OK,
            self.GROUP_URL: HTTPStatus.OK,
            self.POST_URL: HTTPStatus.OK,
            self.PROFILE_URL: HTTPStatus.OK,
            UNEXISTING_URL: HTTPStatus.NOT_FOUND,
            CREATE_URL: HTTPStatus.FOUND,
            self.POSTS_EDIT_URL: HTTPStatus.FOUND
        }
        for adress, status in page_status_codes.items():
            with self.subTest(adress=adress):
                self.assertEqual(Client().get(adress).status_code, status)

    def test_not_author_responses(self):
        page_status_codes = {
            INDEX_URL: HTTPStatus.OK,
            self.GROUP_URL: HTTPStatus.OK,
            self.POST_URL: HTTPStatus.OK,
            self.PROFILE_URL: HTTPStatus.OK,
            UNEXISTING_URL: HTTPStatus.NOT_FOUND,
            CREATE_URL: HTTPStatus.OK,
            self.POSTS_EDIT_URL: HTTPStatus.FOUND
        }
        for adress, status in page_status_codes.items():
            with self.subTest(adress=adress):
                self.assertEqual(
                    self.not_author.get(adress).status_code, status
                )

    def test_author_responses(self):
        page_status_codes = {
            INDEX_URL: HTTPStatus.OK,
            self.GROUP_URL: HTTPStatus.OK,
            self.POST_URL: HTTPStatus.OK,
            self.PROFILE_URL: HTTPStatus.OK,
            UNEXISTING_URL: HTTPStatus.NOT_FOUND,
            CREATE_URL: HTTPStatus.OK,
            self.POSTS_EDIT_URL: HTTPStatus.OK
        }
        for adress, status in page_status_codes.items():
            with self.subTest(adress=adress):
                self.assertEqual(
                    self.authorized_client.get(adress).status_code, status
                )

    def test_urls_use_correct_templates(self):
        templates_url_names = {
            INDEX_URL: 'posts/index.html',
            self.PROFILE_URL: 'posts/profile.html',
            self.GROUP_URL: 'posts/group_list.html',
            self.POST_URL: 'posts/post_detail.html',
            CREATE_URL: 'posts/create_post.html',
            self.POSTS_EDIT_URL: 'posts/create_post.html',
            FOLLOW_URL: 'posts/follow.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                cache.clear()
                self.assertTemplateUsed(
                    self.authorized_client.get(adress),
                    template
                )

    def test_redirects(self):
        redirects = [
            [
                CREATE_URL,
                Client(),
                '/auth/login/?next=/create/'
            ],
            [
                self.POSTS_EDIT_URL,
                Client(),
                f'/auth/login/?next=/posts/{self.post.id}/edit/'
            ],
            [
                self.POSTS_EDIT_URL,
                self.not_author,
                f'/posts/{self.post.id}/'
            ]
        ]
        for url, client, redirect_url in redirects:
            self.assertRedirects(
                client.get(url, follow=True),
                redirect_url
            )
